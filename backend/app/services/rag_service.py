import re
from typing import List, Dict, Any, Optional, TypedDict
from datetime import datetime
from backend.app.core.config import settings
from backend.app.services.vector_store import vector_store
from backend.app.services.llm_provider import get_llm_provider
from backend.app.schemas.domain import QueryResponse, SourceCitation
from backend.app.core.database import SessionLocal
from backend.app.services.temporal_service import get_applicable_evidence
from backend.app.services.compliance_engine import compliance_engine
import logging

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    StateGraph = None
    END = "__end__"

logger = logging.getLogger(__name__)

class RAGState(TypedDict):
    query: str
    system_id: str
    mode: str
    intent: str
    target_date: Optional[datetime]
    target_date_filter: Dict[str, Any]
    retrieved_chunks: List[Dict[str, Any]]
    evidence_score: float
    sources: List[SourceCitation]
    citations: List[str]
    readiness_score: int
    findings: List[Dict[str, Any]]
    highest_risk: str
    answer: str
    confidence: float
    warnings: List[str]
    agent_execution: List[Dict[str, Any]]

class RAGService:
    def __init__(self):
        self.vector_store = vector_store
        self._build_graph()

    def _build_graph(self):
        if StateGraph is None:
            self.graph = None
            return
        workflow = StateGraph(RAGState)
        
        workflow.add_node("supervisor", self._node_supervisor)
        workflow.add_node("evidence", self._node_evidence)
        workflow.add_node("assurance", self._node_assurance)
        workflow.add_node("risk", self._node_risk)
        workflow.add_node("response", self._node_response)
        
        workflow.set_entry_point("supervisor")
        workflow.add_edge("supervisor", "evidence")
        workflow.add_edge("evidence", "assurance")
        workflow.add_edge("assurance", "risk")
        workflow.add_edge("risk", "response")
        workflow.add_edge("response", END)
        
        self.graph = workflow.compile()
        
    def normalize_query(self, query: str) -> str:
        q = query.strip()
        q = re.sub(r'[^\w\s\?-]', ' ', q)
        return ' '.join(q.split())
        
    def _determine_intent(self, query: str) -> str:
        lower_q = query.lower()
        if any(w in lower_q for w in ["audit", "compliance", "finding", "risk", "gate"]):
            return "GxP Audit"
        if "missing" in lower_q or "gap" in lower_q:
            return "Gap Analysis"
        return "General Q&A"
        
    def _determine_scope(self, query: str, default_system: str) -> Dict[str, str]:
        system_id = default_system
        return {"system_id": system_id}
        
    def _determine_filters(self, query: str) -> Dict[str, Any]:
        import dateutil.parser
        
        date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b'
        matches = re.findall(date_pattern, query, re.IGNORECASE)
        
        if matches:
            date_str = matches[0]
            ambiguous = False
            if re.match(r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$', date_str):
                parts = re.split(r'[/-]', date_str)
                p1, p2 = int(parts[0]), int(parts[1])
                if p1 <= 12 and p2 <= 12 and p1 != p2:
                    ambiguous = True
                    
            if ambiguous:
                logger.warning(f"Ambiguous date detected: {date_str}")
                return {
                    "target_date_filter": {
                        "original_value": date_str,
                        "parsed_value": None,
                        "format": "DD/MM/YYYY or MM/DD/YYYY",
                        "ambiguous": True,
                        "confidence": 0.5
                    },
                    "target_date": None
                }
            
            try:
                dt = dateutil.parser.parse(date_str)
                return {
                    "target_date_filter": {
                        "original_value": date_str,
                        "parsed_value": dt.isoformat(),
                        "format": "resolved",
                        "ambiguous": False,
                        "confidence": 1.0
                    },
                    "target_date": dt
                }
            except Exception as e:
                logger.warning(f"Date parsing failed for {date_str}: {e}")
                
        return {}

    def _call_llm_or_reason(self, query: str, context_chunks: List[Dict[str, Any]], mode: str = "General Q&A") -> Dict[str, Any]:
        context_str = "\n\n".join([
            f"--- SOURCE: {c.get('document_title', 'Doc')} (ID: {c.get('document_id', 'DOC')}, Page {c.get('page_number', 1)}, Section: {c.get('section', 'General')}) ---\n{c['content']}"
            for c in context_chunks
        ])

        if not context_chunks:
            return {
                "answer": "UNKNOWN / NOT EVIDENCED: The requested information could not be found in the indexed evidence. No relevant document chunks matched the query and target date.",
                "forced_confidence": 0.30,
                "warnings": ["No matching document chunks found in vector index."]
            }

        provider = get_llm_provider()
        health = provider.health_check()
        if health.get("status") == "Healthy" and health.get("has_api_key"):
            try:
                system_prompt = (
                    "You are the GxP IT Audit & Lifecycle Intelligence Assistant for Novo Nordisk and Novo Life MES PAS-X.\n"
                    "Answer the user's question STRICTLY based on the provided GxP document context below.\n\n"
                    "REGULATORY REASONING RULES:\n"
                    "1. Never hallucinate facts, dates, versions, or approval statuses. If not evidenced, state: 'Not evidenced in the supplied documents.'\n"
                    "2. All evidence must refer to Novo Life MES PAS-X (NL-MES-*) and Governance SOP (HACK-IT-SOP-001).\n"
                    "3. Cite every factual assertion:\n"
                    "   - PDF: [DocumentID | p.Page | Section]\n"
                    "   - Excel: [Workbook | Sheet | Row X]\n"
                    "4. Do NOT claim regulatory compliance or production certification. Use language such as:\n"
                    "   'Evidence indicates alignment', 'Evidence gap identified', 'Requirement not evidenced', 'Potential lifecycle deviation'.\n"
                    "5. When answering audit questions, follow this exact structure:\n"
                    "   ANSWER\n\n"
                    "   Assessment:\n"
                    "   [PASS / PARTIAL / FAIL / NOT EVIDENCED / HOLD / DEFER]\n\n"
                    "   Why:\n"
                    "   ...\n\n"
                    "   Evidence:\n"
                    "   - Document — Page — Section\n\n"
                    "   Gap:\n"
                    "   ...\n\n"
                    "   Risk:\n"
                    "   [CRITICAL / HIGH / MEDIUM / LOW]\n\n"
                    "   Recommendation:\n"
                    "   ...\n\n"
                    "   Confidence:\n"
                    "   [HIGH / MEDIUM / LOW]\n\n"
                    "6. This is a hackathon/training simulation record and does not constitute a regulatory audit or validation decision.\n"
                    "7. DO NOT output internal reasoning blocks or <think> tags. Output only the final response."
                )
                user_prompt = f"CONTEXT:\n{context_str}\n\nUSER QUESTION: {query}\n\nProvide an evidence-backed audit answer:"
                raw_ans = provider.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=settings.AI_TEMPERATURE,
                    max_tokens=settings.AI_MAX_TOKENS
                )
                if raw_ans and len(raw_ans.strip()) > 20:
                    ans_clean = re.sub(r'<think>.*?</think>', '', raw_ans, flags=re.DOTALL).strip()
                    ans_clean = re.sub(r'(?i)Here\'s a thinking process:.*?(?=ANSWER)', '', ans_clean, flags=re.DOTALL).strip()
                    return {"answer": ans_clean, "warnings": []}
            except Exception as e:
                logger.warning(f"OpenRouter LLM generation failed: {e}. Using offline extractive fallback.")

        # Offline fallback
        summary_lines = [
            "OFFLINE EVIDENCE SUMMARY\n",
            "Assessment: UNKNOWN / NOT ASSESSED\n",
            "The local model was unavailable, so this response only summarizes the entire retrieved evidence bundle.\n"
        ]
        
        for idx, chunk in enumerate(context_chunks):
            chunk_meta = chunk.get("metadata", {})
            if "sheet" in chunk_meta and "row" in chunk_meta:
                cite_formatted = f"[{chunk_meta.get('workbook', 'Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx')} | {chunk_meta['sheet']} | Row {chunk_meta['row']}]"
            else:
                cite_formatted = f"[{chunk.get('document_id', 'DOC')} | p.{chunk.get('page_number', 1)} | {chunk.get('section', 'General')}]"
                
            summary_lines.append(f"Evidence {idx + 1}: {cite_formatted}")
            summary_lines.append(f"{chunk.get('content', '')[:450]}...\n")
            
        return {
            "answer": "\n".join(summary_lines)
        }

    def _node_supervisor(self, state: RAGState) -> Dict[str, Any]:
        intent = self._determine_intent(state["query"])
        filters = self._determine_filters(state["query"])
        
        target_date = filters.get("target_date")
        target_date_filter = filters.get("target_date_filter", {})
        
        trace = state.get("agent_execution", []) + [{
            "agent": "Supervisor Agent",
            "step": f"Determined intent as '{intent}' and scoped query to system '{state['system_id']}'.",
            "start": datetime.now().isoformat(),
            "end": datetime.now().isoformat(),
            "result": "Intent and filters extracted."
        }]
        
        return {
            "intent": intent,
            "target_date": target_date,
            "target_date_filter": target_date_filter,
            "agent_execution": trace
        }

    def _node_evidence(self, state: RAGState) -> Dict[str, Any]:
        system_id = state["system_id"]
        target_date = state["target_date"]
        query = state["query"]
        
        db = SessionLocal()
        try:
            valid_evidence_items = get_applicable_evidence(db, system_id, target_date)
            valid_doc_ids = set()
            for e in valid_evidence_items:
                valid_doc_ids.add(e.document_id)
                if getattr(e, "document", None) and getattr(e.document, "document_id", None):
                    valid_doc_ids.add(e.document.document_id)
        finally:
            db.close()
            
        norm_q = self.normalize_query(query)
        retrieved_raw = self.vector_store.hybrid_search(norm_q, system_id=system_id, top_k=20)
        
        filtered_chunks = []
        for ch, score in retrieved_raw:
            if ch.get("document_id") in valid_doc_ids:
                filtered_chunks.append((ch, score))
            if len(filtered_chunks) >= 6:
                break
                
        # Expanded context for GxP Audit
        if state.get("intent") == "GxP Audit" or state.get("mode") == "GxP Audit":
            extra_chunks = self.vector_store.hybrid_search(norm_q, system_id=system_id, top_k=4)
            seen_ids = set([ch.get("id") for ch, _ in filtered_chunks])
            for ch, sc in extra_chunks:
                if ch.get("document_id") not in valid_doc_ids:
                    continue
                if ch.get("id") not in seen_ids:
                    filtered_chunks.append((ch, sc * 0.95))
                    seen_ids.add(ch.get("id"))
            filtered_chunks.sort(key=lambda x: x[1], reverse=True)
            filtered_chunks = filtered_chunks[:6]
            
        sources: List[SourceCitation] = []
        citations: List[str] = []
        retrieved_chunks: List[Dict[str, Any]] = []
        avg_score = 0.0
        
        for ch, score in filtered_chunks:
            doc_name = ch.get("document_title") or "Document"
            doc_id = ch.get("document_id") or "DOC"
            page_num = ch.get("page_number")
            section_name = ch.get("section")
            snippet = ch.get("content", "")[:250].replace("\n", " ")
            chunk_meta = ch.get("metadata", {})
            
            if "sheet" in chunk_meta and "row" in chunk_meta:
                cite_str = f"[{chunk_meta.get('workbook', 'Top_25_Checklists_GxP_IT_Audit_Questions_2026.xlsx')} | {chunk_meta['sheet']} | Row {chunk_meta['row']}]"
            else:
                cite_str = f"[{doc_id} | p.{page_num or 1} | {section_name or 'General'}]"
                
            if cite_str not in citations:
                citations.append(cite_str)
                sources.append(SourceCitation(
                    document=doc_name,
                    page=page_num,
                    section=section_name,
                    snippet=snippet
                ))
            retrieved_chunks.append(ch)
            avg_score += score
            
        if filtered_chunks:
            avg_score = avg_score / len(filtered_chunks)
            
        trace = state.get("agent_execution", []) + [{
            "agent": "Evidence Agent",
            "step": f"Performed hybrid search with temporal filtering.",
            "start": datetime.now().isoformat(),
            "end": datetime.now().isoformat(),
            "evidence_count": str(len(retrieved_chunks)),
            "result": f"Retrieved {len(retrieved_chunks)} valid chunks. (Avg Score: {avg_score:.2f})"
        }]
        
        return {
            "retrieved_chunks": retrieved_chunks,
            "evidence_score": avg_score,
            "sources": sources,
            "citations": citations,
            "agent_execution": trace
        }

    def _node_assurance(self, state: RAGState) -> Dict[str, Any]:
        system_id = state["system_id"]
        db = SessionLocal()
        try:
            comp_res = compliance_engine.evaluate_system(db, system_id)
        finally:
            db.close()
            
        trace = state.get("agent_execution", []) + [{
            "agent": "Assurance Agent",
            "step": "Evaluated configured rules against system state.",
            "start": datetime.now().isoformat(),
            "end": datetime.now().isoformat(),
            "findings_count": str(len(comp_res.get("findings", []))),
            "result": f"Computed readiness score: {comp_res.get('readiness_score', 0)}%"
        }]
        
        return {
            "readiness_score": comp_res.get("readiness_score", 0),
            "findings": comp_res.get("findings", []),
            "agent_execution": trace
        }

    def _node_risk(self, state: RAGState) -> Dict[str, Any]:
        from backend.app.agents.risk_agent import risk_agent
        system_id = state["system_id"]
        findings = state.get("findings", [])
        
        db = SessionLocal()
        try:
            risk_res = risk_agent.run(db, findings, system_id)
            highest_risk = risk_res.metadata.get("highest_risk_level", "LOW")
        except Exception as e:
            highest_risk = "UNKNOWN"
            logger.warning(f"Risk evaluation failed: {e}")
        finally:
            db.close()
            
        trace = state.get("agent_execution", []) + [{
            "agent": "Risk Agent",
            "step": "Consumed findings to produce structured risk context.",
            "start": datetime.now().isoformat(),
            "end": datetime.now().isoformat(),
            "result": f"Highest Risk: {highest_risk}"
        }]
        
        return {
            "highest_risk": highest_risk,
            "agent_execution": trace
        }

    def _node_response(self, state: RAGState) -> Dict[str, Any]:
        retrieved_chunks = state.get("retrieved_chunks", [])
        avg_score = state.get("evidence_score", 0.0)
        
        if not retrieved_chunks or avg_score < 0.40:
            trace = state.get("agent_execution", []) + [{
                "agent": "Response Composer / LLM",
                "step": "Generated response based on missing evidence.",
                "start": datetime.now().isoformat(),
                "end": datetime.now().isoformat(),
                "result": "Response formulated with low confidence."
            }]
            return {
                "answer": "UNKNOWN / NOT EVIDENCED: The requested information could not be found in the indexed evidence. No relevant or applicable document chunks matched the query and target date.",
                "confidence": 0.30,
                "warnings": ["No matching document chunks found or evidence quality is too low."],
                "agent_execution": trace
            }
            
        reasoning_res = self._call_llm_or_reason(state["query"], retrieved_chunks, mode=state["intent"])
        
        if "forced_confidence" in reasoning_res:
            confidence = reasoning_res["forced_confidence"]
        else:
            # Multi-factor confidence model
            retrieval_relevance = min(1.0, avg_score * 1.1)
            temporal_validity = 1.0 if state.get("target_date") else 0.9  # Penalize slightly if no temporal anchor
            source_status = 1.0  # Trust controlled documents
            claim_coverage = min(1.0, len(retrieved_chunks) * 0.25) # Max coverage at 4+ chunks
            conflict_state = 1.0 # Assume deterministic extraction prevents conflict
            
            confidence = (
                retrieval_relevance * 0.40 +
                temporal_validity * 0.20 +
                source_status * 0.20 +
                claim_coverage * 0.10 +
                conflict_state * 0.10
            )
            confidence = min(0.95, max(0.40, confidence))
                
        trace = state.get("agent_execution", []) + [{
            "agent": "Response Composer / LLM",
            "step": "Explained structured results and summarized evidence.",
            "start": datetime.now().isoformat(),
            "end": datetime.now().isoformat(),
            "result": "Human-readable explanation formulated."
        }]
        
        return {
            "answer": reasoning_res["answer"],
            "warnings": reasoning_res.get("warnings", []),
            "confidence": confidence,
            "agent_execution": trace
        }

    def query(self, question: str, system_id: str = "SYS-MES-001", top_k: int = 6, mode: str = "General Q&A") -> QueryResponse:
        initial_state = {
            "query": question,
            "system_id": system_id,
            "mode": mode,
            "intent": "",
            "target_date": None,
            "target_date_filter": {},
            "retrieved_chunks": [],
            "evidence_score": 0.0,
            "sources": [],
            "citations": [],
            "readiness_score": 0,
            "findings": [],
            "highest_risk": "",
            "answer": "",
            "confidence": 0.0,
            "warnings": [],
            "agent_execution": []
        }
        
        if self.graph:
            final_state = self.graph.invoke(initial_state)
        else:
            final_state = initial_state.copy()
            final_state.update(self._node_supervisor(final_state))
            final_state.update(self._node_evidence(final_state))
            final_state.update(self._node_assurance(final_state))
            final_state.update(self._node_risk(final_state))
            final_state.update(self._node_response(final_state))
            
        return QueryResponse(
            query=question,
            answer=final_state["answer"],
            confidence=round(final_state["confidence"], 2),
            sources=final_state["sources"],
            citations=final_state["citations"],
            warnings=final_state.get("warnings", []),
            agent_execution=final_state["agent_execution"]
        )

rag_service = RAGService()

"""
Advanced Claim-Evidence Extractor Tool (CUSTOM TOOL)
Uses spaCy and Sentence Transformers for NLP
"""
from crewai.tools import BaseTool
from typing import Type, List, Dict, Tuple, ClassVar, Set
from pydantic import BaseModel, Field
import spacy
from sentence_transformers import SentenceTransformer
import numpy as np
import re
import json

class ClaimExtractorInput(BaseModel):
    text: str = Field(..., description="Text to analyze for claims and evidence")

class AdvancedClaimExtractor(BaseTool):
    name: str = "Advanced Claim-Evidence Extractor"
    description: str = (
        "Extract factual claims and supporting evidence from text using advanced NLP. "
        "Returns structured JSON with claim-evidence pairs and confidence scores."
    )
    args_schema: Type[BaseModel] = ClaimExtractorInput
    
    # Use ClassVar to indicate these are class-level constants (not Pydantic fields)
    assertion_verbs: ClassVar[Set[str]] = {
        'show', 'demonstrate', 'prove', 'indicate', 'suggest',
        'reveal', 'find', 'discover', 'conclude', 'determine',
        'establish', 'confirm', 'verify', 'report', 'state',
        'argue', 'claim', 'assert', 'maintain', 'contend'
    }
    
    evidence_markers: ClassVar[Set[str]] = {
        'according to', 'research shows', 'studies indicate',
        'data suggests', 'evidence suggests', 'analysis reveals',
        'experiments show', 'surveys find', 'statistics show',
        'researchers found', 'scientists discovered'
    }
    
    def _get_nlp(self):
        """Load spaCy model on demand"""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' not found. "
                "Please run: python -m spacy download en_core_web_sm"
            )
    
    def _get_sentence_model(self):
        """Load sentence transformer on demand"""
        return SentenceTransformer('all-MiniLM-L6-v2')
    
    def preprocess_text(self, text: str) -> List[str]:
        nlp = self._get_nlp()
        text = re.sub(r'\s+', ' ', text)
        doc = nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        sentences = [s for s in sentences if len(s.split()) >= 5]
        return sentences
    
    def is_claim_sentence(self, sentence: str) -> Tuple[bool, float]:
        nlp = self._get_nlp()
        doc = nlp(sentence)
        confidence = 0.0
        
        verbs = {token.lemma_.lower() for token in doc if token.pos_ == "VERB"}
        if verbs & self.assertion_verbs:
            confidence += 0.4
        
        has_subject = any(token.dep_ in ["nsubj", "nsubjpass"] for token in doc)
        if has_subject:
            confidence += 0.2
        
        if doc[-1].text in ['.', '!'] and len(doc) > 5:
            confidence += 0.2
        
        if any(token.like_num or '%' in token.text for token in doc):
            confidence += 0.2
        
        return confidence >= 0.5, confidence
    
    def is_evidence_sentence(self, sentence: str) -> Tuple[bool, float]:
        nlp = self._get_nlp()
        sentence_lower = sentence.lower()
        confidence = 0.0
        
        if any(marker in sentence_lower for marker in self.evidence_markers):
            confidence += 0.5
        
        if re.search(r'\(\d{4}\)|\[\d+\]', sentence):
            confidence += 0.3
        
        doc = nlp(sentence)
        if any(token.like_num for token in doc):
            confidence += 0.2
        
        return confidence >= 0.4, confidence
    
    def calculate_semantic_similarity(self, sent1: str, sent2: str) -> float:
        sentence_model = self._get_sentence_model()
        embeddings = sentence_model.encode([sent1, sent2])
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)
    
    def match_claims_to_evidence(self, claims: List[Dict], evidence: List[Dict]) -> List[Dict]:
        matched_pairs = []
        
        for claim in claims:
            claim_text = claim['text']
            best_evidence = []
            
            for evid in evidence:
                similarity = self.calculate_semantic_similarity(claim_text, evid['text'])
                
                if similarity >= 0.5:
                    best_evidence.append({
                        'text': evid['text'],
                        'confidence': evid['confidence'],
                        'similarity': similarity
                    })
            
            best_evidence.sort(key=lambda x: x['similarity'], reverse=True)
            best_evidence = best_evidence[:3]
            
            matched_pairs.append({
                'claim': claim_text,
                'claim_confidence': claim['confidence'],
                'evidence': best_evidence,
                'evidence_count': len(best_evidence)
            })
        
        return matched_pairs
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        nlp = self._get_nlp()
        doc = nlp(text)
        entities = {}
        
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            if ent.text not in entities[ent.label_]:
                entities[ent.label_].append(ent.text)
        
        return entities
    
    def _run(self, text: str) -> str:
        """
        Main execution method
        """
        try:
            sentences = self.preprocess_text(text)
            
            if not sentences:
                return json.dumps({'error': 'No valid sentences found', 'claims': []})
            
            claims = []
            for sent in sentences:
                is_claim, confidence = self.is_claim_sentence(sent)
                if is_claim:
                    claims.append({'text': sent, 'confidence': confidence})
            
            evidence = []
            for sent in sentences:
                is_evid, confidence = self.is_evidence_sentence(sent)
                if is_evid:
                    evidence.append({'text': sent, 'confidence': confidence})
            
            matched_pairs = self.match_claims_to_evidence(claims, evidence)
            entities = self.extract_entities(text)
            
            result = {
                'summary': {
                    'total_sentences': len(sentences),
                    'claims_found': len(claims),
                    'evidence_found': len(evidence),
                    'matched_pairs': len([p for p in matched_pairs if p['evidence_count'] > 0])
                },
                'claim_evidence_pairs': matched_pairs,
                'entities': entities,
                'metadata': {
                    'model': 'spaCy + SentenceTransformers',
                    'confidence_threshold': 0.5
                }
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({'error': str(e), 'claims': []})
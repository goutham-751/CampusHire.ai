"""
CampusHire.ai Response Evaluator
Advanced scoring and evaluation algorithms for interview responses
"""

import re
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class InterviewEvaluator:
    """
    Advanced evaluation system for interview responses
    Combines AI evaluation with rule-based scoring
    """
    
    def __init__(self):
        # Technical keywords for different domains
        self.technical_keywords = {
            "programming": [
                "algorithm", "data structure", "object-oriented", "functional", "debugging",
                "testing", "unit test", "integration", "api", "database", "sql", "nosql"
            ],
            "web_development": [
                "frontend", "backend", "full-stack", "react", "vue", "angular", "node.js",
                "express", "django", "flask", "rest", "graphql", "microservices"
            ],
            "data_science": [
                "machine learning", "deep learning", "neural network", "pandas", "numpy",
                "tensorflow", "pytorch", "scikit-learn", "data analysis", "visualization"
            ],
            "devops": [
                "docker", "kubernetes", "ci/cd", "jenkins", "git", "aws", "azure", "gcp",
                "terraform", "ansible", "monitoring", "deployment"
            ]
        }
        
        # Quality indicators for responses
        self.quality_indicators = {
            "examples": [
                "for example", "for instance", "in my experience", "when I worked on",
                "at my previous job", "in this project", "specifically", "particularly"
            ],
            "metrics": [
                "increased by", "decreased by", "improved", "reduced", "% improvement",
                "performance gain", "faster", "more efficient", "cost saving"
            ],
            "leadership": [
                "led a team", "managed", "coordinated", "organized", "mentored",
                "trained", "guided", "supervised", "collaborated"
            ],
            "problem_solving": [
                "solved", "resolved", "fixed", "debugged", "optimized", "improved",
                "identified", "analyzed", "troubleshot", "implemented solution"
            ]
        }
    
    def evaluate_response_comprehensively(self, question: str, response: str, 
                                        category: str, ai_evaluation: Dict) -> Dict:
        """
        Combine AI evaluation with rule-based analysis for comprehensive scoring
        """
        
        # Get rule-based metrics
        rule_based_scores = self._calculate_rule_based_scores(response, category)
        
        # Analyze response quality
        quality_metrics = self._analyze_response_quality(response)
        
        # Calculate technical depth
        technical_depth = self._assess_technical_depth(response, category)
        
        # Determine consistency with AI evaluation
        consistency_check = self._check_consistency(ai_evaluation, rule_based_scores)
        
        # Create comprehensive evaluation
        comprehensive_eval = {
            # Core AI scores (from Gemini)
            "ai_overall_score": ai_evaluation.get("overall_score", 5),
            "ai_technical_depth": ai_evaluation.get("technical_depth", 3),
            "ai_communication": ai_evaluation.get("communication_clarity", 3),
            
            # Rule-based scores
            "rule_based_score": rule_based_scores["overall_score"],
            "technical_keyword_score": rule_based_scores["technical_score"],
            "quality_indicator_score": rule_based_scores["quality_score"],
            
            # Quality metrics
            "response_length": quality_metrics["word_count"],
            "sentence_complexity": quality_metrics["avg_sentence_length"],
            "vocabulary_richness": quality_metrics["unique_word_ratio"],
            
            # Technical analysis
            "technical_domain_match": technical_depth["domain_relevance"],
            "technical_keywords_found": technical_depth["keywords_found"],
            
            # Combined final scores
            "final_overall_score": self._calculate_weighted_score(ai_evaluation, rule_based_scores),
            "final_technical_depth": max(ai_evaluation.get("technical_depth", 3), technical_depth["score"]),
            "final_communication": ai_evaluation.get("communication_clarity", 3),
            
            # Quality flags
            "has_specific_examples": quality_metrics["has_examples"],
            "mentions_metrics": quality_metrics["has_metrics"],
            "shows_leadership": quality_metrics["shows_leadership"],
            "demonstrates_problem_solving": quality_metrics["shows_problem_solving"],
            
            # Evaluation metadata
            "consistency_score": consistency_check["consistency"],
            "evaluation_confidence": consistency_check["confidence"],
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        
        return comprehensive_eval
    
    def calculate_interview_aggregate_scores(self, all_responses: List[Dict]) -> Dict:
        """
        Calculate aggregate performance metrics across all interview responses
        """
        
        if not all_responses:
            return self._empty_aggregate_scores()
        
        # Extract all scores
        overall_scores = []
        technical_scores = []
        communication_scores = []
        category_performance = {}
        
        for response in all_responses:
            eval_data = response.get("evaluation", {})
            
            # Collect scores
            overall_scores.append(eval_data.get("final_overall_score", eval_data.get("overall_score", 5)))
            technical_scores.append(eval_data.get("final_technical_depth", eval_data.get("technical_depth", 3)))
            communication_scores.append(eval_data.get("final_communication", eval_data.get("communication_clarity", 3)))
            
            # Category-wise performance
            category = response.get("category", "general")
            if category not in category_performance:
                category_performance[category] = []
            category_performance[category].append(eval_data.get("overall_score", 5))
        
        # Calculate statistics
        aggregate_scores = {
            "overall_statistics": {
                "mean": self._safe_mean(overall_scores),
                "median": self._safe_median(overall_scores),
                "std_deviation": self._safe_std(overall_scores),
                "min_score": min(overall_scores) if overall_scores else 0,
                "max_score": max(overall_scores) if overall_scores else 0,
                "score_range": max(overall_scores) - min(overall_scores) if overall_scores else 0
            },
            
            "technical_statistics": {
                "mean": self._safe_mean(technical_scores),
                "consistency": 1 - (self._safe_std(technical_scores) / 5) if technical_scores else 0
            },
            
            "communication_statistics": {
                "mean": self._safe_mean(communication_scores),
                "consistency": 1 - (self._safe_std(communication_scores) / 5) if communication_scores else 0
            },
            
            "category_performance": {
                category: {
                    "average_score": self._safe_mean(scores),
                    "response_count": len(scores),
                    "performance_level": self._categorize_performance(self._safe_mean(scores))
                }
                for category, scores in category_performance.items()
            },
            
            "improvement_trend": self._calculate_improvement_trend(overall_scores),
            
            "performance_consistency": self._calculate_consistency_rating(overall_scores),
            
            "red_flags": self._identify_red_flags(all_responses),
            
            "standout_indicators": self._identify_standout_indicators(all_responses)
        }
        
        return aggregate_scores
    
    def generate_scoring_insights(self, aggregate_scores: Dict) -> Dict:
        """
        Generate actionable insights from scoring analysis
        """
        
        overall_stats = aggregate_scores.get("overall_statistics", {})
        mean_score = overall_stats.get("mean", 0)
        consistency = aggregate_scores.get("performance_consistency", 0)
        
        insights = {
            "performance_level": self._categorize_performance(mean_score),
            
            "key_insights": [],
            
            "hiring_recommendation": self._generate_hiring_recommendation(mean_score, consistency),
            
            "development_areas": self._identify_development_areas(aggregate_scores),
            
            "interview_quality_assessment": self._assess_interview_quality(aggregate_scores),
            
            "confidence_level": self._calculate_overall_confidence(aggregate_scores)
        }
        
        # Generate specific insights
        if mean_score >= 8:
            insights["key_insights"].append("Consistently strong performance across all areas")
        elif mean_score >= 6:
            insights["key_insights"].append("Solid overall performance with some standout responses")
        elif mean_score >= 4:
            insights["key_insights"].append("Mixed performance - shows potential but needs development")
        else:
            insights["key_insights"].append("Performance below expectations - significant development needed")
        
        if consistency >= 0.8:
            insights["key_insights"].append("Highly consistent response quality")
        elif consistency >= 0.6:
            insights["key_insights"].append("Generally consistent with occasional variations")
        else:
            insights["key_insights"].append("Inconsistent response quality - may indicate nervousness or knowledge gaps")
        
        return insights
    
    # Private helper methods
    
    def _calculate_rule_based_scores(self, response: str, category: str) -> Dict:
        """Calculate scores based on rule-based analysis"""
        
        response_lower = response.lower()
        
        # Technical keyword scoring
        technical_score = 0
        total_keywords = 0
        
        for domain, keywords in self.technical_keywords.items():
            for keyword in keywords:
                if keyword in response_lower:
                    technical_score += 1
                total_keywords += 1
        
        technical_score = min(5, (technical_score / max(total_keywords, 1)) * 10)
        
        # Quality indicator scoring
        quality_score = 0
        for indicator_type, indicators in self.quality_indicators.items():
            for indicator in indicators:
                if indicator in response_lower:
                    quality_score += 1
        
        quality_score = min(5, quality_score)
        
        # Length and structure scoring
        word_count = len(response.split())
        length_score = min(5, max(1, (word_count - 20) / 40 * 4 + 1))
        
        # Calculate overall rule-based score
        overall_score = (technical_score + quality_score + length_score) / 3
        
        return {
            "overall_score": overall_score,
            "technical_score": technical_score,
            "quality_score": quality_score,
            "length_score": length_score
        }
    
    def _analyze_response_quality(self, response: str) -> Dict:
        """Analyze qualitative aspects of the response"""
        
        words = response.split()
        sentences = re.split(r'[.!?]+', response)
        unique_words = set(word.lower().strip('.,!?;:') for word in words)
        
        response_lower = response.lower()
        
        return {
            "word_count": len(words),
            "sentence_count": len([s for s in sentences if s.strip()]),
            "avg_sentence_length": len(words) / max(1, len([s for s in sentences if s.strip()])),
            "unique_word_ratio": len(unique_words) / max(1, len(words)),
            "has_examples": any(indicator in response_lower for indicator in self.quality_indicators["examples"]),
            "has_metrics": any(indicator in response_lower for indicator in self.quality_indicators["metrics"]),
            "shows_leadership": any(indicator in response_lower for indicator in self.quality_indicators["leadership"]),
            "shows_problem_solving": any(indicator in response_lower for indicator in self.quality_indicators["problem_solving"])
        }
    
    def _assess_technical_depth(self, response: str, category: str) -> Dict:
        """Assess technical depth and domain relevance"""
        
        response_lower = response.lower()
        keywords_found = []
        domain_scores = {}
        
        for domain, keywords in self.technical_keywords.items():
            score = sum(1 for keyword in keywords if keyword in response_lower)
            domain_scores[domain] = score
            if score > 0:
                keywords_found.extend([kw for kw in keywords if kw in response_lower])
        
        # Determine most relevant domain
        best_domain = max(domain_scores.items(), key=lambda x: x[1]) if domain_scores else ("general", 0)
        
        # Calculate technical depth score
        tech_score = min(5, max(1, best_domain[1] * 1.5))
        
        return {
            "score": tech_score,
            "domain_relevance": best_domain[0],
            "keywords_found": keywords_found[:10],  # Limit to top 10
            "domain_scores": domain_scores
        }
    
    def _check_consistency(self, ai_eval: Dict, rule_eval: Dict) -> Dict:
        """Check consistency between AI and rule-based evaluations"""
        
        ai_score = ai_eval.get("overall_score", 5)
        rule_score = rule_eval.get("overall_score", 5)
        
        difference = abs(ai_score - rule_score)
        consistency = max(0, 1 - (difference / 10))  # Normalize to 0-1
        
        confidence = "high" if consistency >= 0.8 else "medium" if consistency >= 0.6 else "low"
        
        return {
            "consistency": consistency,
            "confidence": confidence,
            "score_difference": difference
        }
    
    def _calculate_weighted_score(self, ai_eval: Dict, rule_eval: Dict) -> float:
        """Calculate weighted final score combining AI and rule-based evaluations"""
        
        ai_score = ai_eval.get("overall_score", 5)
        rule_score = rule_eval.get("overall_score", 5)
        
        # Weight AI evaluation more heavily (70%) but incorporate rule-based validation (30%)
        weighted_score = (ai_score * 0.7) + (rule_score * 0.3)
        
        return min(10, max(1, weighted_score))
    
    def _safe_mean(self, values: List[float]) -> float:
        """Calculate mean safely"""
        return sum(values) / len(values) if values else 0
    
    def _safe_median(self, values: List[float]) -> float:
        """Calculate median safely"""
        if not values:
            return 0
        sorted_values = sorted(values)
        n = len(sorted_values)
        return sorted_values[n//2] if n % 2 == 1 else (sorted_values[n//2-1] + sorted_values[n//2]) / 2
    
    def _safe_std(self, values: List[float]) -> float:
        """Calculate standard deviation safely"""
        if len(values) < 2:
            return 0
        mean = self._safe_mean(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def _categorize_performance(self, score: float) -> str:
        """Categorize performance level"""
        if score >= 8:
            return "excellent"
        elif score >= 6:
            return "good"
        elif score >= 4:
            return "average"
        else:
            return "below_average"
    
    def _calculate_improvement_trend(self, scores: List[float]) -> str:
        """Calculate if candidate improved during interview"""
        if len(scores) < 3:
            return "insufficient_data"
        
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        first_avg = self._safe_mean(first_half)
        second_avg = self._safe_mean(second_half)
        
        if second_avg > first_avg + 0.5:
            return "improving"
        elif second_avg < first_avg - 0.5:
            return "declining"
        else:
            return "stable"
    
    def _calculate_consistency_rating(self, scores: List[float]) -> float:
        """Calculate consistency rating (0-1)"""
        if len(scores) < 2:
            return 1.0
        
        std_dev = self._safe_std(scores)
        max_possible_std = 4.5  # Theoretical max std dev for scores 1-10
        
        return max(0, 1 - (std_dev / max_possible_std))
    
    def _identify_red_flags(self, responses: List[Dict]) -> List[str]:
        """Identify potential red flags in responses"""
        
        red_flags = []
        
        # Check for very short responses
        short_responses = sum(1 for r in responses if len(r.get("response_text", "").split()) < 15)
        if short_responses >= len(responses) * 0.4:  # 40% or more short responses
            red_flags.append("Multiple very brief responses - may indicate lack of depth")
        
        # Check for consistently low scores
        low_scores = sum(1 for r in responses if r.get("evaluation", {}).get("overall_score", 5) < 4)
        if low_scores >= len(responses) * 0.5:  # 50% or more low scores
            red_flags.append("Consistently low performance across multiple areas")
        
        # Check for lack of examples
        no_examples = sum(1 for r in responses 
                         if not r.get("evaluation", {}).get("has_specific_examples", False))
        if no_examples >= len(responses) * 0.7:  # 70% or more without examples
            red_flags.append("Lack of specific examples or concrete experience")
        
        return red_flags
    
    def _identify_standout_indicators(self, responses: List[Dict]) -> List[str]:
        """Identify positive standout indicators"""
        
        indicators = []
        
        # Check for high scores
        high_scores = sum(1 for r in responses if r.get("evaluation", {}).get("overall_score", 5) >= 8)
        if high_scores >= len(responses) * 0.4:  # 40% or more high scores
            indicators.append("Multiple excellent responses demonstrating strong competency")
        
        # Check for technical depth
        technical_responses = sum(1 for r in responses 
                                if r.get("evaluation", {}).get("technical_depth", 3) >= 4)
        if technical_responses >= len(responses) * 0.3:  # 30% or more technically strong
            indicators.append("Strong technical knowledge and depth")
        
        # Check for leadership examples
        leadership_responses = sum(1 for r in responses 
                                 if r.get("evaluation", {}).get("shows_leadership", False))
        if leadership_responses >= 2:
            indicators.append("Demonstrates leadership experience and skills")
        
        return indicators
    
    def _generate_hiring_recommendation(self, mean_score: float, consistency: float) -> str:
        """Generate hiring recommendation based on scores"""
        
        if mean_score >= 7.5 and consistency >= 0.7:
            return "Strong Hire - Excellent candidate with consistent performance"
        elif mean_score >= 6.5 and consistency >= 0.6:
            return "Hire - Good candidate with solid performance"
        elif mean_score >= 5.5:
            return "Maybe - Average candidate, consider specific role requirements"
        else:
            return "Pass - Performance below expectations for this role"
    
    def _identify_development_areas(self, aggregate_scores: Dict) -> List[str]:
        """Identify key development areas"""
        
        areas = []
        
        tech_stats = aggregate_scores.get("technical_statistics", {})
        comm_stats = aggregate_scores.get("communication_statistics", {})
        
        if tech_stats.get("mean", 0) < 3:
            areas.append("Technical skills and knowledge")
        
        if comm_stats.get("mean", 0) < 3:
            areas.append("Communication and articulation")
        
        if aggregate_scores.get("performance_consistency", 0) < 0.6:
            areas.append("Consistency and confidence in responses")
        
        return areas
    
    def _assess_interview_quality(self, aggregate_scores: Dict) -> str:
        """Assess overall quality of the interview data"""
        
        response_count = sum(cat_data.get("response_count", 0) 
                           for cat_data in aggregate_scores.get("category_performance", {}).values())
        
        consistency = aggregate_scores.get("performance_consistency", 0)
        
        if response_count >= 5 and consistency >= 0.7:
            return "High quality interview with reliable data"
        elif response_count >= 3 and consistency >= 0.5:
            return "Good quality interview with actionable insights"
        else:
            return "Limited interview data - consider additional assessment"
    
    def _calculate_overall_confidence(self, aggregate_scores: Dict) -> float:
        """Calculate confidence in the evaluation"""
        
        consistency = aggregate_scores.get("performance_consistency", 0)
        response_count = sum(cat_data.get("response_count", 0) 
                           for cat_data in aggregate_scores.get("category_performance", {}).values())
        
        # Base confidence on consistency and amount of data
        base_confidence = consistency * 0.7
        data_confidence = min(0.3, (response_count / 10) * 0.3)
        
        return min(1.0, base_confidence + data_confidence)
    
    def _empty_aggregate_scores(self) -> Dict:
        """Return empty aggregate scores structure"""
        
        return {
            "overall_statistics": {"mean": 0, "median": 0, "std_deviation": 0, "min_score": 0, "max_score": 0, "score_range": 0},
            "technical_statistics": {"mean": 0, "consistency": 0},
            "communication_statistics": {"mean": 0, "consistency": 0},
            "category_performance": {},
            "improvement_trend": "no_data",
            "performance_consistency": 0,
            "red_flags": ["No interview responses to evaluate"],
            "standout_indicators": []
        }

# Convenience functions for easy import
def evaluate_response(question: str, response: str, category: str, ai_evaluation: Dict) -> Dict:
    """Convenience function for response evaluation"""
    evaluator = InterviewEvaluator()
    return evaluator.evaluate_response_comprehensively(question, response, category, ai_evaluation)

def calculate_aggregate_scores(responses: List[Dict]) -> Dict:
    """Convenience function for aggregate scoring"""
    evaluator = InterviewEvaluator()
    return evaluator.calculate_interview_aggregate_scores(responses)

def generate_insights(aggregate_scores: Dict) -> Dict:
    """Convenience function for insight generation"""
    evaluator = InterviewEvaluator()
    return evaluator.generate_scoring_insights(aggregate_scores)

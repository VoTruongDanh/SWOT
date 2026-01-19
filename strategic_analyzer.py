"""
Strategic Analyzer Module - Enterprise-level SWOT Analysis Tools
Provides TOWS Matrix, Priority Scoring, Risk Assessment, and Action Planning
"""
from typing import Dict, List, Any, Optional
import pandas as pd


class StrategicAnalyzer:
    """Enterprise-level strategic analysis tools for SWOT"""
    
    # Weights for priority scoring
    DEFAULT_WEIGHTS = {
        'impact': 0.4,
        'feasibility': 0.3,
        'urgency': 0.3
    }
    
    # Impact level to score mapping
    IMPACT_SCORES = {
        'High': 9,
        'Medium': 5,
        'Low': 2
    }
    
    # Risk level mapping
    RISK_SCORES = {
        'High': 9,
        'Medium': 5,
        'Low': 2
    }
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize Strategic Analyzer
        
        Args:
            weights: Custom weights for priority calculation
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
    
    def calculate_priority_score(self, item: Dict[str, Any], category: str) -> float:
        """
        Calculate priority score for a SWOT item
        Score = Impact × Feasibility × Urgency (weighted)
        
        Args:
            item: SWOT item dict
            category: 'Strengths', 'Weaknesses', 'Opportunities', 'Threats'
        
        Returns:
            Priority score (0-10)
        """
        # Get base impact score
        impact_level = item.get('impact') or item.get('risk_level', 'Medium')
        impact_score = self.IMPACT_SCORES.get(impact_level, 5)
        
        # Estimate feasibility based on category and content
        if category == 'Strengths':
            # Strengths are already feasible to leverage
            feasibility = 8
            urgency = 6  # Medium urgency to leverage
        elif category == 'Weaknesses':
            # Weaknesses may be harder to fix
            improvement_cost = item.get('improvement_cost', 'Medium')
            feasibility = {'Low': 8, 'Medium': 5, 'High': 3}.get(improvement_cost, 5)
            urgency = 7  # Higher urgency to fix
        elif category == 'Opportunities':
            # Opportunities have time sensitivity
            time_to_capture = item.get('time_to_capture', 'Medium term')
            urgency = {'Short term': 9, 'Medium term': 6, 'Long term': 3}.get(time_to_capture, 6)
            investment = item.get('required_investment', 'Medium')
            feasibility = {'Low': 8, 'Medium': 5, 'High': 3}.get(investment, 5)
        else:  # Threats
            probability = item.get('probability', 'Medium')
            severity = item.get('severity', 'Medium')
            prob_score = self.RISK_SCORES.get(probability, 5)
            sev_score = self.RISK_SCORES.get(severity, 5)
            urgency = (prob_score + sev_score) / 2
            feasibility = 5  # Neutral for threats
        
        # Calculate weighted score
        score = (
            impact_score * self.weights['impact'] +
            feasibility * self.weights['feasibility'] +
            urgency * self.weights['urgency']
        )
        
        # Normalize to 0-10 scale
        return round(min(10, max(0, score)), 1)
    
    def generate_tows_matrix(self, swot_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Generate TOWS Matrix from SWOT data
        Creates strategic combinations: SO, WO, ST, WT strategies
        
        Args:
            swot_data: Dict containing SWOT_Analysis
        
        Returns:
            Dict with SO_Strategies, WO_Strategies, ST_Strategies, WT_Strategies
        """
        swot = swot_data.get('SWOT_Analysis', {})
        strengths = swot.get('Strengths', [])
        weaknesses = swot.get('Weaknesses', [])
        opportunities = swot.get('Opportunities', [])
        threats = swot.get('Threats', [])
        
        tows = {
            'SO_Strategies': [],  # Maxi-Maxi: Use Strengths to capture Opportunities
            'WO_Strategies': [],  # Mini-Maxi: Overcome Weaknesses to capture Opportunities
            'ST_Strategies': [],  # Maxi-Mini: Use Strengths to counter Threats
            'WT_Strategies': []   # Mini-Mini: Minimize Weaknesses to avoid Threats
        }
        
        # Generate SO Strategies (Aggressive/Growth strategies)
        if strengths and opportunities:
            top_strengths = sorted(strengths, 
                key=lambda x: self.IMPACT_SCORES.get(x.get('impact', 'Medium'), 5), 
                reverse=True)[:3]
            top_opportunities = sorted(opportunities,
                key=lambda x: x.get('priority_score', 5),
                reverse=True)[:3]
            
            for s in top_strengths:
                for o in top_opportunities:
                    strategy = {
                        'strategy': f"Tận dụng '{s.get('topic', '')}' để nắm bắt '{o.get('topic', '')}'",
                        'strength_used': s.get('topic', ''),
                        'opportunity_captured': o.get('topic', ''),
                        'priority': 'High' if s.get('impact') == 'High' and o.get('priority_score', 0) > 7 else 'Medium'
                    }
                    if len(tows['SO_Strategies']) < 5:
                        tows['SO_Strategies'].append(strategy)
        
        # Generate WO Strategies (Turnaround strategies)
        if weaknesses and opportunities:
            top_weaknesses = sorted(weaknesses,
                key=lambda x: self.IMPACT_SCORES.get(x.get('impact', 'Medium'), 5),
                reverse=True)[:3]
            
            for w in top_weaknesses:
                for o in top_opportunities if 'top_opportunities' in dir() else opportunities[:3]:
                    strategy = {
                        'strategy': f"Khắc phục '{w.get('topic', '')}' bằng cách tận dụng '{o.get('topic', '')}'",
                        'weakness_addressed': w.get('topic', ''),
                        'opportunity_used': o.get('topic', ''),
                        'priority': 'High' if w.get('impact') == 'High' else 'Medium'
                    }
                    if len(tows['WO_Strategies']) < 5:
                        tows['WO_Strategies'].append(strategy)
        
        # Generate ST Strategies (Diversification strategies)
        if strengths and threats:
            top_threats = sorted(threats,
                key=lambda x: self.RISK_SCORES.get(x.get('risk_level', 'Medium'), 5),
                reverse=True)[:3]
            
            for s in top_strengths if 'top_strengths' in dir() else strengths[:3]:
                for t in top_threats:
                    strategy = {
                        'strategy': f"Sử dụng '{s.get('topic', '')}' để đối phó '{t.get('topic', '')}'",
                        'strength_used': s.get('topic', ''),
                        'threat_countered': t.get('topic', ''),
                        'priority': 'High' if t.get('risk_level') == 'High' else 'Medium'
                    }
                    if len(tows['ST_Strategies']) < 5:
                        tows['ST_Strategies'].append(strategy)
        
        # Generate WT Strategies (Defensive strategies)
        if weaknesses and threats:
            for w in top_weaknesses if 'top_weaknesses' in dir() else weaknesses[:3]:
                for t in top_threats if 'top_threats' in dir() else threats[:3]:
                    strategy = {
                        'strategy': f"Giảm thiểu '{w.get('topic', '')}' để tránh bị ảnh hưởng bởi '{t.get('topic', '')}'",
                        'weakness_addressed': w.get('topic', ''),
                        'threat_mitigated': t.get('topic', ''),
                        'priority': 'High' if w.get('impact') == 'High' and t.get('risk_level') == 'High' else 'Medium'
                    }
                    if len(tows['WT_Strategies']) < 5:
                        tows['WT_Strategies'].append(strategy)
        
        return tows
    
    def create_action_plan(self, swot_data: Dict[str, Any], 
                          tows_matrix: Dict[str, List[Dict]] = None) -> List[Dict]:
        """
        Create strategic action plan with timeline, KPIs, and ownership
        
        Args:
            swot_data: Dict containing SWOT_Analysis
            tows_matrix: Optional TOWS matrix for strategy-based actions
        
        Returns:
            List of action items with timeline, KPIs, owner, etc.
        """
        actions = []
        swot = swot_data.get('SWOT_Analysis', {})
        
        # Priority counter for ordering
        priority = 1
        
        # Define timeline phases
        timelines = ['Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026']
        
        # Define role assignments based on action type
        role_mapping = {
            'quality': 'Operations Manager',
            'service': 'Customer Service Manager', 
            'marketing': 'Marketing Manager',
            'price': 'Finance Manager',
            'product': 'Product Manager',
            'staff': 'HR Manager',
            'digital': 'IT Manager',
            'brand': 'Marketing Manager',
            'default': 'General Manager'
        }
        
        # Generate actions from high-impact Strengths (leverage)
        for item in swot.get('Strengths', []):
            if item.get('impact') == 'High':
                action = {
                    'action': f"Tăng cường và quảng bá: {item.get('topic', '')}",
                    'type': 'Leverage Strength',
                    'priority': priority,
                    'timeline': timelines[min(priority - 1, 3)],
                    'owner_role': self._get_owner_role(item.get('topic', ''), role_mapping),
                    'kpis': item.get('kpi_metrics', ['Customer satisfaction score', 'Market share']),
                    'estimated_investment': 'Medium',
                    'expected_outcome': item.get('leverage_strategy', 'Tận dụng điểm mạnh để tăng trưởng'),
                    'status': 'Planned'
                }
                actions.append(action)
                priority += 1
                if priority > 10:
                    break
        
        # Generate actions from high-impact Weaknesses (improve)
        for item in swot.get('Weaknesses', []):
            if item.get('impact') == 'High':
                action = {
                    'action': f"Cải thiện: {item.get('topic', '')}",
                    'type': 'Address Weakness',
                    'priority': priority,
                    'timeline': timelines[min(priority - 1, 3)],
                    'owner_role': self._get_owner_role(item.get('topic', ''), role_mapping),
                    'kpis': ['Improvement rate', 'Customer feedback score'],
                    'estimated_investment': item.get('improvement_cost', 'Medium'),
                    'expected_outcome': item.get('mitigation_plan', 'Khắc phục điểm yếu'),
                    'root_cause': item.get('root_cause', 'Chưa xác định'),
                    'status': 'Planned'
                }
                actions.append(action)
                priority += 1
                if priority > 15:
                    break
        
        # Generate actions from Opportunities (capture)
        for item in swot.get('Opportunities', []):
            if item.get('priority_score', 0) >= 7 or item.get('action_idea'):
                action = {
                    'action': f"Nắm bắt cơ hội: {item.get('topic', '')}",
                    'type': 'Capture Opportunity',
                    'priority': priority,
                    'timeline': timelines[min(priority - 1, 3)],
                    'owner_role': self._get_owner_role(item.get('topic', ''), role_mapping),
                    'kpis': ['New revenue', 'Market penetration'],
                    'estimated_investment': item.get('required_investment', 'Medium'),
                    'expected_outcome': item.get('action_idea', 'Tận dụng cơ hội thị trường'),
                    'market_size': item.get('market_size', 'Medium'),
                    'status': 'Planned'
                }
                actions.append(action)
                priority += 1
                if priority > 20:
                    break
        
        # Generate actions from high-risk Threats (mitigate)
        for item in swot.get('Threats', []):
            if item.get('risk_level') == 'High':
                action = {
                    'action': f"Phòng ngừa rủi ro: {item.get('topic', '')}",
                    'type': 'Mitigate Threat',
                    'priority': priority,
                    'timeline': timelines[0],  # Urgent
                    'owner_role': self._get_owner_role(item.get('topic', ''), role_mapping),
                    'kpis': ['Risk reduction rate', 'Incident count'],
                    'estimated_investment': 'Medium',
                    'expected_outcome': item.get('contingency_plan', 'Giảm thiểu rủi ro'),
                    'probability': item.get('probability', 'Medium'),
                    'severity': item.get('severity', 'Medium'),
                    'status': 'Urgent'
                }
                actions.append(action)
                priority += 1
        
        # Sort by priority
        actions.sort(key=lambda x: x['priority'])
        
        return actions[:20]  # Limit to top 20 actions
    
    def _get_owner_role(self, topic: str, role_mapping: Dict[str, str]) -> str:
        """Determine owner role based on topic keywords"""
        topic_lower = topic.lower()
        
        for keyword, role in role_mapping.items():
            if keyword in topic_lower:
                return role
        
        return role_mapping['default']
    
    def assess_risks(self, threats: List[Dict]) -> List[Dict]:
        """
        Create risk assessment matrix for threats
        
        Args:
            threats: List of threat items
        
        Returns:
            List of threats with risk scores and recommendations
        """
        assessed_risks = []
        
        for threat in threats:
            probability = threat.get('probability', 'Medium')
            severity = threat.get('severity', threat.get('risk_level', 'Medium'))
            
            prob_score = self.RISK_SCORES.get(probability, 5)
            sev_score = self.RISK_SCORES.get(severity, 5)
            
            # Calculate composite risk score
            risk_score = (prob_score * sev_score) / 10  # Scale to 0-8.1
            
            # Determine risk category
            if risk_score >= 6:
                risk_category = 'Critical'
                recommendation = 'Cần hành động ngay lập tức, ưu tiên cao nhất'
            elif risk_score >= 4:
                risk_category = 'High'
                recommendation = 'Cần lập kế hoạch ứng phó trong vòng 30 ngày'
            elif risk_score >= 2:
                risk_category = 'Medium'
                recommendation = 'Theo dõi và chuẩn bị phương án dự phòng'
            else:
                risk_category = 'Low'
                recommendation = 'Theo dõi định kỳ, không cần hành động ngay'
            
            assessed_risk = {
                **threat,
                'probability_score': prob_score,
                'severity_score': sev_score,
                'composite_risk_score': round(risk_score, 2),
                'risk_category': risk_category,
                'recommendation': recommendation
            }
            assessed_risks.append(assessed_risk)
        
        # Sort by risk score descending
        assessed_risks.sort(key=lambda x: x['composite_risk_score'], reverse=True)
        
        return assessed_risks
    
    def competitive_positioning(self, my_shop_data: Dict, competitor_data: Dict = None) -> Dict:
        """
        Analyze competitive positioning based on SWOT data
        
        Args:
            my_shop_data: SWOT data for my shop
            competitor_data: Optional SWOT data for competitor
        
        Returns:
            Dict with competitive scores and analysis
        """
        # Define dimensions for competitive analysis
        dimensions = ['quality', 'price', 'service', 'location', 'brand', 'innovation']
        
        my_scores = {}
        competitor_scores = {}
        
        swot = my_shop_data.get('SWOT_Analysis', {})
        strengths = swot.get('Strengths', [])
        weaknesses = swot.get('Weaknesses', [])
        
        # Expanded keywords for better detection
        # Expanded keywords (English + Vietnamese) for better detection
        keywords = {
            'quality': ['quality', 'taste', 'fresh', 'delicious', 'premium', 'standard',
                       'chất lượng', 'ngon', 'vị', 'tươi', 'menu', 'đồ uống', 'bánh', 'sản phẩm', 'đậm đà'],
            'price': ['price', 'cost', 'expensive', 'cheap', 'affordable', 'value', 'money',
                     'giá', 'chi phí', 'đắt', 'rẻ', 'hợp lý', 'tiền', 'ví', 'khuyến mãi'],
            'service': ['service', 'staff', 'friendly', 'slow', 'fast', 'attitude',
                       'phục vụ', 'nhân viên', 'thái độ', 'chậm', 'nhanh', 'thân thiện', 'dịch vụ', 'order', 'nhiệt tình'],
            'location': ['location', 'place', 'parking', 'space', 'view', 'center',
                        'vị trí', 'không gian', 'chỗ ngồi', 'view', 'đẹp', 'thoáng', 'gửi xe', 'bãi xe', 'trang trí', 'decor'],
            'brand': ['brand', 'reputation', 'image', 'famous', 'popular', 'known', 'marketing', 'awareness',
                     'thương hiệu', 'nổi tiếng', 'uy tín', 'quen thuộc', 'hình ảnh', 'tin dùng'],
            'innovation': ['innovation', 'creative', 'new', 'unique', 'technology', 'app', 'digital',
                          'mới lạ', 'sáng tạo', 'app', 'công nghệ', 'độc đáo', 'khác biệt', 'trend', 'xu hướng']
        }

        # Calculate scores based on SWOT items
        for dim in dimensions:
            dim_lower = dim.lower()
            dim_keywords = keywords.get(dim_lower, [dim_lower])
            
            # Start with neutral baseline
            strength_score = 5
            
            # Check strengths for this dimension
            for s in strengths:
                text = (s.get('topic', '') + ' ' + s.get('description', '')).lower()
                if any(k in text for k in dim_keywords):
                    # Boost score based on impact
                    impact_boost = {
                        'High': 4,      # 5 + 4 = 9 (Excellent)
                        'Medium': 2,    # 5 + 2 = 7 (Good)
                        'Low': 1        # 5 + 1 = 6 (Above Avg)
                    }.get(s.get('impact', 'Medium'), 2)
                    strength_score = max(strength_score, 5 + impact_boost)
            
            # Check weaknesses for this dimension
            weakness_penalty = 0
            for w in weaknesses:
                text = (w.get('topic', '') + ' ' + w.get('description', '')).lower()
                if any(k in text for k in dim_keywords):
                    # Penalize score based on impact
                    penalty = {
                        'High': 3,      # 5 - 3 = 2 (Poor)
                        'Medium': 2,    # 5 - 2 = 3 (Below Avg)
                        'Low': 1        # 5 - 1 = 4 (Slightly Below)
                    }.get(w.get('impact', 'Medium'), 2)
                    weakness_penalty = max(weakness_penalty, penalty)
            
            # Final My Score: Baseline + Boost - Penalty
            # Use max/min to keep within 1-10 range logic effectively
            if weakness_penalty > 0 and strength_score == 5:
                # Only weakness found
                my_scores[dim] = max(1, 5 - weakness_penalty)
            elif weakness_penalty > 0 and strength_score > 5:
                # Both strength and weakness found (mixed)
                my_scores[dim] = max(1, strength_score - weakness_penalty)
            else:
                # Only strength or neutral
                my_scores[dim] = strength_score
        
        # Estimate competitor scores from threats and opportunities
        threats = swot.get('Threats', [])
        opportunities = swot.get('Opportunities', [])
        
        for dim in dimensions:
            dim_lower = dim.lower()
            dim_keywords = keywords.get(dim_lower, [dim_lower])
            
            comp_score = 5  # Start with neutral baseline
            
            # Threats indicate competitor strengths
            for t in threats:
                text = (t.get('topic', '') + ' ' + t.get('description', '')).lower()
                
                # Special check for 'Big Competitor' markers in threats -> implies strong competitor brand
                if dim == 'brand' and any(x in text for x in ['big', 'major', 'chain', 'franchise', 'giant', 'leader']):
                    comp_score = max(comp_score, 9)
                
                elif any(k in text for k in dim_keywords):
                    risk_boost = {
                        'High': 3,      # 5 + 3 = 8 (Strong Competitor)
                        'Medium': 2,    # 5 + 2 = 7 (Good Competitor)
                        'Low': 1        # 5 + 1 = 6 (Above Avg)
                    }.get(t.get('risk_level', 'Medium'), 2)
                    comp_score = max(comp_score, 5 + risk_boost)
            
            # Opportunities may indicate competitor weaknesses (market gaps)
            for o in opportunities:
                text = (o.get('topic', '') + ' ' + o.get('description', '')).lower()
                if any(k in text for k in dim_keywords):
                    # Reduce competitor score if there's an opportunity here
                    # e.g. "Competitors ignore X" or "Gap in X"
                    gap_deduction = {
                        'High': 2,    # 5 - 2 = 3 (Weak Competitor)
                        'Medium': 1,  # 5 - 1 = 4 (Below Avg)
                    }.get(o.get('priority', 'Medium') if 'priority' in o else 'Medium', 1)
                    
                    # Apply deduction only if we haven't already identified it as a strength via threats
                    if comp_score == 5:
                         comp_score = max(1, 5 - gap_deduction)
                    
            competitor_scores[dim] = comp_score

        
        # Calculate overall scores
        my_overall = sum(my_scores.values()) / len(dimensions)
        comp_overall = sum(competitor_scores.values()) / len(dimensions)
        
        return {
            'my_scores': my_scores,
            'competitor_scores': competitor_scores,
            'my_overall': round(my_overall, 1),
            'competitor_overall': round(comp_overall, 1),
            'dimensions': dimensions,
            'competitive_advantage': my_overall > comp_overall,
            'advantage_gaps': {
                dim: my_scores[dim] - competitor_scores[dim] 
                for dim in dimensions
            }
        }


def enrich_swot_with_scores(swot_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich SWOT data with priority scores and additional analysis
    
    Args:
        swot_data: Original SWOT data from AI
    
    Returns:
        Enriched SWOT data with priority scores
    """
    analyzer = StrategicAnalyzer()
    enriched = swot_data.copy()
    
    swot = enriched.get('SWOT_Analysis', {})
    
    # Add priority scores to each category
    for category in ['Strengths', 'Weaknesses', 'Opportunities', 'Threats']:
        items = swot.get(category, [])
        for item in items:
            if 'priority_score' not in item:
                item['priority_score'] = analyzer.calculate_priority_score(item, category)
    
    # Generate TOWS Matrix
    enriched['TOWS_Matrix'] = analyzer.generate_tows_matrix(enriched)
    
    # Create Action Plan
    enriched['Strategic_Action_Plan'] = analyzer.create_action_plan(enriched, enriched['TOWS_Matrix'])
    
    # Assess Risks
    if swot.get('Threats'):
        enriched['Risk_Assessment'] = analyzer.assess_risks(swot['Threats'])
    
    # Competitive Positioning
    # Ưu tiên lấy từ AI nếu có, nếu không thì tự tính toán
    calculated_competitive = analyzer.competitive_positioning(enriched)
    
    if 'Competitive_Analysis' in enriched and isinstance(enriched['Competitive_Analysis'], dict):
        ai_competitive = enriched['Competitive_Analysis']
        # Merge: AI scores take precedence, but keep calculated structure if missing
        if 'my_scores' in ai_competitive:
            calculated_competitive['my_scores'].update(ai_competitive['my_scores'])
        if 'competitor_scores' in ai_competitive:
            calculated_competitive['competitor_scores'].update(ai_competitive['competitor_scores'])
            
        # Re-calculate averages
        avg_my = sum(calculated_competitive['my_scores'].values()) / 6
        avg_comp = sum(calculated_competitive['competitor_scores'].values()) / 6
        calculated_competitive['my_overall'] = round(avg_my, 1)
        calculated_competitive['competitor_overall'] = round(avg_comp, 1)
        calculated_competitive['competitive_advantage'] = avg_my > avg_comp
        calculated_competitive['advantage_gaps'] = {
            dim: calculated_competitive['my_scores'][dim] - calculated_competitive['competitor_scores'][dim]
            for dim in calculated_competitive['dimensions']
        }
    
    enriched['Competitive_Analysis'] = calculated_competitive
    
    return enriched

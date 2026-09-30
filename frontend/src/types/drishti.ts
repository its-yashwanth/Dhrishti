/**
 * Drishti Domain Types
 * Strict typing reflecting backend agent contracts and ML cascade outputs.
 */

export type TradeFlow = 'Export' | 'Import';
export type ShockDirection = 'supply_contraction' | 'supply_shock' | 'demand_contraction' | 'demand_shock' | 'trade_restriction' | 'logistics_disruption';
export type SeverityLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'VERY HIGH' | 'CRITICAL' | 'INFO';

export interface StructuredEvent {
  country: string;
  commodity: string;
  hs4: number;
  trade_type: TradeFlow;
  event_type: string;
  shock_direction: ShockDirection;
  approximate_timing: string;
  summary: string;
  confidence: 'high' | 'medium' | 'low';
  shock_intensity?: number;
  trade_share?: number;
  extracted_from?: string;
}

export interface ModelAPrediction {
  Trade_Return_1M_Pred: number;
  status: 'AVAILABLE' | 'UNAVAILABLE';
  model_name: string;
  provenance: string;
  features_used?: Record<string, number | string>;
  metrics?: {
    r2?: number;
    mae?: number;
  };
}

export interface ModelBPrediction {
  Production_Growth_Pred: number;
  Production_Risk: 'Low' | 'Medium' | 'High' | 'Severe';
  status: 'AVAILABLE' | 'UNAVAILABLE';
  model_name: string;
  provenance: string;
}

export interface ModelCPrediction {
  Price_Return_1M_Pred: number | null;
  status: 'AVAILABLE' | 'UNAVAILABLE';
  model_name: string;
  provenance: string;
  note?: string;
}

export interface ModelDPrediction {
  Agri_GVA_Growth_Pred: number;
  Inflation_Change_Pred: number;
  status: 'AVAILABLE' | 'UNAVAILABLE';
  model_name: string;
  provenance: string;
}

export interface MLPredictions {
  trade: ModelAPrediction;
  agriculture: ModelBPrediction;
  price: ModelCPrediction;
  economy: ModelDPrediction;
}

export interface PortNode {
  port: string;
  state?: string;
  risk_level: SeverityLevel;
  betweenness_centrality?: number;
  cargo_share_pct?: number;
  composite_importance?: number;
  identification_basis?: string;
  note?: string;
  provenance?: string;
  lat?: number;
  lon?: number;
}

export interface AlternativePath {
  source_port: string;
  alternate_port: string;
  state?: string;
  affinity_score: number;
  handling_capacity_pct?: number;
  redundancy_status: 'Viable Alternative' | 'Secondary Option' | 'High Congestion';
}

export interface SupplyChainRiskIndicator {
  indicator: string;
  level: SeverityLevel;
  value: string | number;
  note: string;
  provenance: string;
}

export interface SupplyChainAnalysis {
  commodity: string;
  trade_flow: TradeFlow;
  event_country: string;
  critical_ports: PortNode[];
  alternative_paths: AlternativePath[];
  risk_indicators: SupplyChainRiskIndicator[];
  scenario_exposure: {
    effective_shock: number;
    max_port_exposure?: number;
    max_state_exposure?: number;
    max_district_exposure?: number;
    n_ports_in_propagation?: number;
    n_states_in_propagation?: number;
    n_districts_in_propagation?: number;
    top_exposed_districts?: Array<{ district: string; state: string; exposure: number }>;
    disclaimer?: string;
  };
  network_resilience: {
    resilience_score?: number;
    hhi_index?: number;
    network_bottlenecks?: number;
    status_summary?: string;
  };
  limitations?: string[];
  provenance_tags?: Record<string, string>;
}

export interface VulnerableRegion {
  district: string;
  state: string;
  ravs: number;
  classification: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY HIGH';
  production_share: number;
  yield_cv: number;
  production_cv: number;
  crop_area_concentration: number;
  hhi?: number;
  trend?: string;
  scenario_exposure?: number;
}

export interface StateVulnerabilitySummary {
  state: string;
  mean_ravs: number;
  classification: 'LOW' | 'MODERATE' | 'HIGH' | 'VERY HIGH';
  n_districts: number;
  top_district: string;
  max_ravs: number;
}

export interface VulnerabilityAnalysis {
  commodity: string;
  hs4: number;
  matched_crops: string[];
  crop_resolution: string;
  trade_type: TradeFlow;
  shock_direction: ShockDirection;
  latest_year_in_data: string | number;
  year_used: string;
  n_districts_analysed: number;
  n_states_analysed: number;
  top_vulnerable_regions: VulnerableRegion[];
  state_scores_summary?: StateVulnerabilitySummary[];
  regional_scores_summary: {
    mean_ravs: number;
    max_ravs: number;
    min_ravs: number;
    std_ravs: number;
    percentile_75_ravs: number;
    score_range: string;
  };
  ravs_methodology: {
    formula: string;
    weights: Record<string, number>;
  };
  limitations?: string[];
  disclaimer?: string;
}

export interface StakeholderImpactItem {
  stakeholder: string;
  role: string;
  severity: SeverityLevel;
  direction: 'Negative' | 'Positive' | 'Mixed' | 'Neutral';
  score?: number;
  impact_summary: string;
  detailed_rationale: string;
  transmission_channels?: string[];
  evidence_sources: string[];
  provenance: string;
}

export interface MitigationActionItem {
  id: string;
  time_horizon: 'Immediate (0-30d)' | 'Short-Term (1-3m)' | 'Medium-Term (3-6m)' | 'Long-Term (6-12m)';
  action: string;
  target_stakeholder: string;
  rationale: string;
  policy_lever: string;
  confidence: 'High' | 'Medium' | 'Low';
  provenance: string;
  expected_outcome?: string;
}

export interface EvidenceItem {
  id: string;
  source: string;
  source_type: 'Government Statistical Dataset' | 'ML Econometric Model' | 'GDELT News MCP' | 'MultiDiGraph Analytics' | 'Deterministic Engine' | 'LLM Synthesis';
  title: string;
  evidence: string;
  used_for: string;
  coverage_period?: string;
  provenance_tag: string;
  citation?: string;
  relevance_score?: number;
}

export interface DrishtiAnalysisResult {
  scenario_name: string;
  scenario_data: {
    query: string;
    event_country: string;
    commodity: string;
    hs4: number;
    trade_type: TradeFlow;
    event_type: string;
    shock_direction: ShockDirection;
    shock_intensity: number;
    trade_share: number;
    description: string;
    confidence: 'high' | 'medium' | 'low';
    event_date: string;
  };
  ml_predictions: MLPredictions;
  provenance_counts?: Record<string, number>;
  provenance_details?: Record<string, any>;
  economic_interpretation: string;
  stakeholder_impacts: Record<string, any> | StakeholderImpactItem[];
  historical_context?: {
    analogs_identified?: number;
    relevant_events?: Array<{ event: string; year: number; similarity: string; lesson: string }>;
  };
  mitigation_actions: MitigationActionItem[];
  supply_chain_analysis: {
    supply_chain_analysis?: SupplyChainAnalysis;
    provenance?: any[];
  } | any;
  vulnerability_analysis: {
    vulnerability_analysis?: VulnerabilityAnalysis;
    provenance?: any[];
  } | any;
  llm_usage?: {
    economic_interpretation?: string;
    mitigation?: string;
  };
  evidence_list?: EvidenceItem[];
  timestamp?: string;
}

export interface ScenarioInputParams {
  query: string;
  partner_country?: string;
  commodity?: string;
  trade_type?: TradeFlow;
  shock_intensity?: number;
  trade_share?: number;
  hs4?: number;
}

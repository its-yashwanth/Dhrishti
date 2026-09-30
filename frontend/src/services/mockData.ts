import { DrishtiAnalysisResult, StructuredEvent } from '../types/drishti';

export const DEFAULT_STRUCTURED_EVENT: StructuredEvent = {
  country: 'RUSSIA',
  commodity: 'Wheat',
  hs4: 1001,
  trade_type: 'Export',
  event_type: 'Trade Restriction / Export Ban',
  shock_direction: 'supply_contraction',
  approximate_timing: 'Q2 2024 / Immediate',
  summary: 'Russia suspended import permissions for Indian wheat consignments following sanitary certifications and regional trade recalibrations, triggering port backlog and immediate export contraction.',
  confidence: 'high',
  shock_intensity: 1.5,
  trade_share: 5.0,
  extracted_from: 'Natural language analysis cross-referenced with GDELT DOC 2.0 and UN Comtrade baseline'
};

export const MOCK_ANALYSIS_RESULT: DrishtiAnalysisResult = {
  scenario_name: 'Wheat Export Disruption (India -> Russia)',
  timestamp: new Date().toISOString(),
  scenario_data: {
    query: 'Russia stopped importing wheat from India',
    event_country: 'RUSSIA',
    commodity: 'Wheat',
    hs4: 1001,
    trade_type: 'Export',
    event_type: 'trade_restriction',
    shock_direction: 'supply_contraction',
    shock_intensity: 1.5,
    trade_share: 5.0,
    description: 'Bilateral export restriction on Indian wheat to Russia with 1.5x shock multiplier across 5.0% historical bilateral share baseline.',
    confidence: 'high',
    event_date: '2024-06-15'
  },
  ml_predictions: {
    trade: {
      Trade_Return_1M_Pred: -4.82,
      status: 'AVAILABLE',
      model_name: 'Model A — Trade Return RF/Ridge Estimator',
      provenance: '[ML INFERENCE: XGBoost + Random Forest Ensemble]',
      metrics: {
        r2: 0.68,
        mae: 1.14
      },
      features_used: {
        'Effective_Shock': 0.075,
        'Goldstein_Score': -4.5,
        'Avg_Tone': -3.2,
        'Trade_Share': 5.0,
        'Lagged_Trade_Return_1M': -0.42
      }
    },
    agriculture: {
      Production_Growth_Pred: -1.35,
      Production_Risk: 'Medium',
      status: 'AVAILABLE',
      model_name: 'Model B — Agricultural Production Gradient Booster',
      provenance: '[ML INFERENCE: LightGBM Regressor]'
    },
    price: {
      Price_Return_1M_Pred: -2.18,
      status: 'AVAILABLE',
      model_name: 'Model C — Domestic Wholesale Price Vector Autoregressor',
      provenance: '[ML INFERENCE: Multi-lag Ridge Estimator]',
      note: 'Negative price return reflects domestic supply diversion due to trapped export volumes in major northern mandis.'
    },
    economy: {
      Agri_GVA_Growth_Pred: -0.41,
      Inflation_Change_Pred: -0.19,
      status: 'AVAILABLE',
      model_name: 'Model D — Macroeconomic GVA & Inflation Transfer Model',
      provenance: '[ML INFERENCE: Econometric Elasticity Matrix]'
    }
  },
  economic_interpretation: 'Econometric forecasts indicate an associated 1-month export flow contraction of -4.82% for Wheat to Russia. Domestic mandis in surplus northern zones are projected to face short-run accumulation pressure (-2.18% domestic price deflection). National agricultural production shows a projected growth deflection of -1.35% with moderate vulnerability. Macro agricultural GVA growth is associated with a -0.41 percentage point dampening, alongside an estimated -0.19 pp easing of immediate food inflation pressures due to localized cereal availability.',
  stakeholder_impacts: [
    {
      stakeholder: 'Farmers',
      role: 'Primary Producers & Mandi Sellers',
      severity: 'HIGH',
      direction: 'Negative',
      score: 74,
      impact_summary: 'Localized farm-gate price discount in primary wheat-belt mandis due to diverted export volumes.',
      detailed_rationale: 'Growers in high-export surplus districts face localized procurement delays. While national MSP provides a price floor, private procurement premiums will evaporate, reducing net realized farmer margin by an estimated 6–9%.',
      transmission_channels: ['Mandi gate price discount', 'Private procurement withdrawal', 'Warehouse storage cost inflation'],
      evidence_sources: ['Model C Wholesale Price Forecast', 'State Mandi Arrival Records', 'DES Agri Statistics'],
      provenance: '[DETERMINISTIC STAKEHOLDER ENGINE]'
    },
    {
      stakeholder: 'Exporters & Grain Traders',
      role: 'Agri-Logistics & International Trading Houses',
      severity: 'CRITICAL',
      direction: 'Negative',
      score: 88,
      impact_summary: 'Direct contract cancellation, port demurrage fees, and working capital lockup.',
      detailed_rationale: 'Active shipping consignments scheduled for Black Sea and St. Petersburg discharge face immediate rerouting or cancellation. Exporters bear container turnaround fees and port warehousing costs at Kandla and Mundra.',
      transmission_channels: ['Export revenue loss', 'Port demurrage accrual', 'Letter of Credit settlement disputes'],
      evidence_sources: ['Model A Trade Contraction (-4.82%)', 'MoPSW Port Statistics', 'DGFT Export Declarations'],
      provenance: '[DETERMINISTIC STAKEHOLDER ENGINE]'
    },
    {
      stakeholder: 'Domestic Consumers',
      role: 'Urban & Rural Food Consumers',
      severity: 'LOW',
      direction: 'Positive',
      score: 28,
      impact_summary: 'Slight easing of retail flour (Atta) and cereal inflation in consumption centers.',
      detailed_rationale: 'Diverted grain retains more wheat within the domestic supply chain, stabilizing retail flour prices and mitigating short-term inflationary pressure on household food baskets.',
      transmission_channels: ['Retail flour price stabilization', 'Increased domestic milling buffer'],
      evidence_sources: ['Model D Food Inflation Delta (-0.19 pp)', 'Consumer Food Price Index'],
      provenance: '[DETERMINISTIC STAKEHOLDER ENGINE]'
    },
    {
      stakeholder: 'Importers (Foreign Market)',
      role: 'Destination Grain Buyers & Processors',
      severity: 'HIGH',
      direction: 'Negative',
      score: 72,
      impact_summary: 'Supply procurement disruption forcing immediate sourcing pivot to Australia or North America.',
      detailed_rationale: 'Russian flour millers and animal feed processors face immediate supply deficit, incurring spot premiums for alternative ocean freight.',
      transmission_channels: ['International spot freight surge', 'Alternative bilateral procurement lead-times'],
      evidence_sources: ['UN Comtrade Bilateral Matrix', 'Global Grain Exchange Indexes'],
      provenance: '[DETERMINISTIC STAKEHOLDER ENGINE]'
    },
    {
      stakeholder: 'Regional Economies',
      role: 'State Agri-Belts (Punjab, Haryana, MP, Gujarat)',
      severity: 'MODERATE',
      direction: 'Mixed',
      score: 61,
      impact_summary: 'Asymmetric impact concentrated in western gateway ports and northern grain-belt hubs.',
      detailed_rationale: 'Punjab and Haryana face freight yard congestion; Gujarat and Maharashtra port clusters experience handling volume shocks, whereas southern non-wheat states remain largely insulated.',
      transmission_channels: ['Logistics hub backlogs', 'State agricultural market committee cess receipts'],
      evidence_sources: ['Vulnerability Agent RAVS Rankings', 'MoPSW Port Handling Statistics'],
      provenance: '[DETERMINISTIC STAKEHOLDER ENGINE]'
    },
    {
      stakeholder: 'Government & Policymakers',
      role: 'Department of Commerce & Food Corporation of India (FCI)',
      severity: 'MODERATE',
      direction: 'Neutral',
      score: 55,
      impact_summary: 'Required open-market sale adjustments and buffer stock re-absorption.',
      detailed_rationale: 'FCI must assess whether to expand decentralized procurement to absorb stranded export-grade wheat, balancing fiscal subsidy costs against farm income stabilization.',
      transmission_channels: ['Central buffer stock inventory expansion', 'Export incentive re-calibration', 'WTO notification requirements'],
      evidence_sources: ['Model D Agri GVA Impact (-0.41%)', 'FCI Monthly Stock Bulletin'],
      provenance: '[DETERMINISTIC STAKEHOLDER ENGINE]'
    }
  ],
  historical_context: {
    analogs_identified: 3,
    relevant_events: [
      {
        event: '2022 Black Sea Wheat Export Corridor Suspension',
        year: 2022,
        similarity: '87% structural match (wheat export restriction with ocean freight rerouting)',
        lesson: 'Directing unexported volumes into domestic strategic reserves prevented farm-gate collapse while alternative MENA export channels took 45 days to activate.'
      },
      {
        event: '2020 India Non-Basmati Rice Port Congestion & Container Shortage',
        year: 2020,
        similarity: '74% logistics similarity (port cargo stagnation at Kandla & JNPA)',
        lesson: 'Early diversion of cargo to minor ports (Pipavav, Mundra) reduced demurrage by 34%.'
      },
      {
        event: '2018 Russia-Turkey Agricultural Tariff Sanctions',
        year: 2018,
        similarity: '69% bilateral policy match',
        lesson: 'Currency swap mechanisms and third-party transit trade stabilized flow within 3 months.'
      }
    ]
  },
  mitigation_actions: [
    {
      id: 'mit-1',
      time_horizon: 'Immediate (0-30d)',
      action: 'Activate FCI Open Market Buffer Stock Absorption Protocol',
      target_stakeholder: 'Farmers & Mandi Traders',
      rationale: 'Prevent distress selling by issuing authorized procurement mandates for export-grade wheat at MSP+ quality bonus in primary affected clusters (Punjab, Haryana, MP).',
      policy_lever: 'FCI Decentralized Procurement & Price Stabilization Fund (PSF)',
      confidence: 'High',
      provenance: '[HISTORICAL PRECEDENT 2022 + ML CASCADE]',
      expected_outcome: 'Protects farm-gate returns within 3% of baseline; absorbs up to 450,000 MT of stranded grain.'
    },
    {
      id: 'mit-2',
      time_horizon: 'Immediate (0-30d)',
      action: 'Port Demurrage Waiver & Inland Container Depot (ICD) Buffer Rerouting',
      target_stakeholder: 'Exporters & Freight Forwarders',
      rationale: 'Instruct Major Port Trusts (Deendayal/Kandla, JNPA) to freeze demurrage penalties for 21 days for verified export-halted consignments.',
      policy_lever: 'Ministry of Ports, Shipping and Waterways (MoPSW) Circular',
      confidence: 'High',
      provenance: '[SUPPLY CHAIN NETWORK GRAPH ANALYSIS]',
      expected_outcome: 'Saves exporters an estimated ₹45 crore in non-operational detention fees.'
    },
    {
      id: 'mit-3',
      time_horizon: 'Short-Term (1-3m)',
      action: 'Fast-Track Destination Diversification to MENA & Southeast Asian Sourcing Corridors',
      target_stakeholder: 'Exporters & Department of Commerce',
      rationale: 'Engage bilateral phytosanitary fast-tracking with alternative importers (Egypt, Indonesia, UAE) exhibiting active deficit signals.',
      policy_lever: 'APEDA Agri-Exchange Trade Delegation & Bilateral Trade Protocols',
      confidence: 'Medium',
      provenance: '[UN COMTRADE FLOW MATRIX + ML MODEL A]',
      expected_outcome: 'Recovers 65–75% of displaced export volumes within 60 days.'
    },
    {
      id: 'mit-4',
      time_horizon: 'Medium-Term (3-6m)',
      action: 'Expand Domestic Food Processing & Roller Flour Mill Credit Lines',
      target_stakeholder: 'Domestic Millers & Consumers',
      rationale: 'Incentivize domestic secondary processing of high-protein wheat through working capital interest subvention for millers.',
      policy_lever: 'Ministry of Food Processing Industries (MoFPI) Credit Subvention',
      confidence: 'Medium',
      provenance: '[ECONOMIC INTERPRETATION AGENT]',
      expected_outcome: 'Transforms raw grain surplus into shelf-stable packaged flour and bakery products.'
    },
    {
      id: 'mit-5',
      time_horizon: 'Long-Term (6-12m)',
      action: 'Multi-Modal Port Redundancy & Agricultural Export Cold-Chain Corridors',
      target_stakeholder: 'Infrastructure & Regional Economies',
      rationale: 'Reduce high port cargo concentration (HHI > 0.45) at Kandla by developing dedicated western agri-rail freight corridors to Pipavav and JNPA.',
      policy_lever: 'PM Gati Shakti National Master Plan for Multi-modal Connectivity',
      confidence: 'High',
      provenance: '[NETWORK RESILIENCE ANALYSIS]',
      expected_outcome: 'Enhances national agricultural export resilience against single-port geopolitical disruptions.'
    }
  ],
  supply_chain_analysis: {
    supply_chain_analysis: {
      commodity: 'Wheat',
      trade_flow: 'Export',
      event_country: 'RUSSIA',
      critical_ports: [
        {
          port: 'Deendayal Port Authority (Kandla)',
          state: 'Gujarat',
          risk_level: 'HIGH',
          betweenness_centrality: 0.428,
          cargo_share_pct: 38.4,
          composite_importance: 0.88,
          identification_basis: 'Bottleneck & Primary Agri-Cargo Hub',
          note: 'Handles ~38% of northern Indian agricultural exports to Eastern Europe & Central Asia. Highest scenario-exposed bottleneck.',
          provenance: '[GRAPH-DERIVED] + [PORT DATA: MoPSW 2023-24]',
          lat: 23.0033,
          lon: 70.2189
        },
        {
          port: 'Jawaharlal Nehru Port Authority (JNPA)',
          state: 'Maharashtra',
          risk_level: 'MODERATE',
          betweenness_centrality: 0.385,
          cargo_share_pct: 26.2,
          composite_importance: 0.79,
          identification_basis: 'Container Terminal & Multi-modal Rail Head',
          note: 'Containerized grain handling node. Moderate exposure; viable modeled alternative handling port.',
          provenance: '[GRAPH-DERIVED] + [PORT DATA: MoPSW 2023-24]',
          lat: 18.9499,
          lon: 72.9515
        },
        {
          port: 'Mundra Port',
          state: 'Gujarat',
          risk_level: 'HIGH',
          betweenness_centrality: 0.312,
          cargo_share_pct: 18.5,
          composite_importance: 0.74,
          identification_basis: 'Private Deep-Draft Agri Terminal',
          note: 'Direct rail connectivity from Haryana and Punjab. Scenario-exposed to Russian route cancellations.',
          provenance: '[GRAPH-DERIVED]',
          lat: 22.7389,
          lon: 69.7042
        },
        {
          port: 'Mumbai Port Authority',
          state: 'Maharashtra',
          risk_level: 'LOW',
          betweenness_centrality: 0.142,
          cargo_share_pct: 6.8,
          composite_importance: 0.48,
          identification_basis: 'Secondary General Cargo',
          note: 'Low scenario exposure; limited dedicated bulk grain loading infrastructure.',
          provenance: '[GRAPH-DERIVED]',
          lat: 18.9633,
          lon: 72.8532
        },
        {
          port: 'Paradip Port Authority',
          state: 'Odisha',
          risk_level: 'LOW',
          betweenness_centrality: 0.089,
          cargo_share_pct: 4.1,
          composite_importance: 0.35,
          identification_basis: 'Eastern Seaboard Bulk Port',
          note: 'Primary focus on minerals and coastal rice; minimal direct wheat exposure to European Russia.',
          provenance: '[GRAPH-DERIVED]',
          lat: 20.2644,
          lon: 86.6713
        }
      ],
      alternative_paths: [
        {
          source_port: 'Deendayal Port Authority',
          alternate_port: 'Jawaharlal Nehru Port Authority (JNPA)',
          state: 'Maharashtra',
          affinity_score: 0.94,
          handling_capacity_pct: 82,
          redundancy_status: 'Viable Alternative'
        },
        {
          source_port: 'Deendayal Port Authority',
          alternate_port: 'Mundra Port (Adani Ports)',
          state: 'Gujarat',
          affinity_score: 0.89,
          handling_capacity_pct: 75,
          redundancy_status: 'Viable Alternative'
        },
        {
          source_port: 'Deendayal Port Authority',
          alternate_port: 'Pipavav Port',
          state: 'Gujarat',
          affinity_score: 0.78,
          handling_capacity_pct: 54,
          redundancy_status: 'Secondary Option'
        }
      ],
      risk_indicators: [
        {
          indicator: 'Trade Share Exposure',
          level: 'MODERATE',
          value: '5.0%',
          note: 'Partner-country share of relevant Indian export baseline exposure.',
          provenance: '[USER / CLI PARAMETER] → [GRAPH-DERIVED]'
        },
        {
          indicator: 'Effective Shock Exposure',
          level: 'MODERATE',
          value: '0.0750',
          note: 'Effective shock = 0.0750 (shock_intensity 1.50 × trade_share 5.0%).',
          provenance: '[USER / CLI PARAMETER] → [GRAPH-DERIVED]'
        },
        {
          indicator: 'Port Bottleneck Exposure',
          level: 'HIGH',
          value: '2 Ports Flagged',
          note: '2 potential port bottlenecks identified. Top: Deendayal Port Authority (HIGH).',
          provenance: '[GRAPH-DERIVED] + [PORT DATA]'
        },
        {
          indicator: 'Port Cargo Concentration (HHI)',
          level: 'INFO',
          value: '0.4128',
          note: 'Port cargo HHI = 0.4128. Indicates moderate-to-high cargo concentration in western gateway terminals.',
          provenance: '[GRAPH-DERIVED] + [PORT DATA]'
        },
        {
          indicator: 'ML Model A — Trade Signal',
          level: 'HIGH',
          value: '-4.82%',
          note: 'Model A projects -4.82% trade return. Negative values correspond to export contraction.',
          provenance: '[ML MODEL OUTPUT]'
        },
        {
          indicator: 'ML Model B — Production Signal',
          level: 'MODERATE',
          value: '-1.35% | Risk: Medium',
          note: 'Model B national production growth forecast: -1.35%, Risk classification: Medium.',
          provenance: '[ML MODEL OUTPUT]'
        }
      ],
      scenario_exposure: {
        effective_shock: 0.075,
        max_port_exposure: 0.428,
        max_state_exposure: 0.384,
        max_district_exposure: 0.142,
        n_ports_in_propagation: 5,
        n_states_in_propagation: 4,
        n_districts_in_propagation: 24,
        top_exposed_districts: [
          { district: 'Firozpur', state: 'Punjab', exposure: 0.142 },
          { district: 'Karnal', state: 'Haryana', exposure: 0.128 },
          { district: 'Ludhiana', state: 'Punjab', exposure: 0.119 },
          { district: 'Hardoi', state: 'Uttar Pradesh', exposure: 0.104 }
        ],
        disclaimer: 'Modeled scenario exposure is derived from NetworkX MultiDiGraph propagation using historical trade affinity and port cargo statistics. It represents modeled exposure, not verified physical container routes.'
      },
      network_resilience: {
        resilience_score: 0.64,
        hhi_index: 0.4128,
        network_bottlenecks: 2,
        status_summary: 'Moderate network resilience. Western seaboard has viable alternative handling paths (JNPA, Pipavav) but faces potential rail corridor congestion.'
      },
      limitations: [
        'Port cargo statistics reflect annual aggregated metrics from MoPSW (2023-24 / 2024-25).',
        'Commodity-port affinity is algorithmically inferred from port bulk handling specialization.',
        'Alternative handling paths represent modeled topological redundancy, not live commercial berth availability.'
      ]
    },
    provenance: [
      {
        source_type: '[PORT DATA]',
        dataset: 'port_statistics.csv',
        origin: 'Ministry of Ports, Shipping and Waterways (MoPSW)',
        years: '2023-24, 2024-25'
      },
      {
        source_type: '[GRAPH-DERIVED]',
        description: 'NetworkX MultiDiGraph analytics, centrality scoring, and shock propagation',
        graph_type: 'Heterogeneous, weighted, directed MultiDiGraph (48 nodes, 61 edges)'
      }
    ]
  },
  vulnerability_analysis: {
    vulnerability_analysis: {
      commodity: 'Wheat',
      hs4: 1001,
      matched_crops: ['Wheat'],
      crop_resolution: 'Exact Match',
      trade_type: 'Export',
      shock_direction: 'supply_contraction',
      latest_year_in_data: '2022-23',
      year_used: '2017-18 to 2022-23',
      n_districts_analysed: 320,
      n_states_analysed: 18,
      regional_scores_summary: {
        mean_ravs: 0.412,
        max_ravs: 0.841,
        min_ravs: 0.082,
        std_ravs: 0.163,
        percentile_75_ravs: 0.548,
        score_range: '0.0820 – 0.8410'
      },
      ravs_methodology: {
        formula: 'RAVS = 0.35 * ProdShare + 0.30 * YieldCV + 0.20 * ProdCV + 0.15 * CropAreaConc',
        weights: {
          production_share: 0.35,
          yield_instability: 0.30,
          production_instability: 0.20,
          crop_area_concentration: 0.15
        }
      },
      top_vulnerable_regions: [
        {
          district: 'Firozpur',
          state: 'Punjab',
          ravs: 0.841,
          classification: 'VERY HIGH',
          production_share: 4.82,
          yield_cv: 0.194,
          production_cv: 0.221,
          crop_area_concentration: 0.782,
          hhi: 0.624,
          trend: 'Increasing Vulnerability (+4.2%)',
          scenario_exposure: 0.142
        },
        {
          district: 'Karnal',
          state: 'Haryana',
          ravs: 0.796,
          classification: 'VERY HIGH',
          production_share: 4.15,
          yield_cv: 0.178,
          production_cv: 0.205,
          crop_area_concentration: 0.741,
          hhi: 0.598,
          trend: 'Stable High (+0.8%)',
          scenario_exposure: 0.128
        },
        {
          district: 'Ludhiana',
          state: 'Punjab',
          ravs: 0.764,
          classification: 'VERY HIGH',
          production_share: 3.91,
          yield_cv: 0.162,
          production_cv: 0.198,
          crop_area_concentration: 0.718,
          hhi: 0.572,
          trend: 'Decreasing Vulnerability (-1.4%)',
          scenario_exposure: 0.119
        },
        {
          district: 'Hardoi',
          state: 'Uttar Pradesh',
          ravs: 0.728,
          classification: 'HIGH',
          production_share: 3.42,
          yield_cv: 0.231,
          production_cv: 0.264,
          crop_area_concentration: 0.645,
          hhi: 0.495,
          trend: 'Increasing Instability (+6.1%)',
          scenario_exposure: 0.104
        },
        {
          district: 'Sangrur',
          state: 'Punjab',
          ravs: 0.711,
          classification: 'HIGH',
          production_share: 3.35,
          yield_cv: 0.151,
          production_cv: 0.183,
          crop_area_concentration: 0.769,
          hhi: 0.612,
          trend: 'Stable (+0.3%)',
          scenario_exposure: 0.098
        },
        {
          district: 'Aligarh',
          state: 'Uttar Pradesh',
          ravs: 0.685,
          classification: 'HIGH',
          production_share: 2.89,
          yield_cv: 0.218,
          production_cv: 0.242,
          crop_area_concentration: 0.618,
          hhi: 0.462,
          trend: 'Increasing Instability (+3.5%)',
          scenario_exposure: 0.089
        },
        {
          district: 'Baran',
          state: 'Rajasthan',
          ravs: 0.654,
          classification: 'HIGH',
          production_share: 2.21,
          yield_cv: 0.274,
          production_cv: 0.298,
          crop_area_concentration: 0.584,
          hhi: 0.412,
          trend: 'Climate Sensitive (+7.8%)',
          scenario_exposure: 0.076
        },
        {
          district: 'Hoshangabad (Narmadapuram)',
          state: 'Madhya Pradesh',
          ravs: 0.638,
          classification: 'HIGH',
          production_share: 2.76,
          yield_cv: 0.189,
          production_cv: 0.215,
          crop_area_concentration: 0.662,
          hhi: 0.508,
          trend: 'Rapid Yield Expansion (+5.4%)',
          scenario_exposure: 0.084
        },
        {
          district: 'Meerut',
          state: 'Uttar Pradesh',
          ravs: 0.582,
          classification: 'MODERATE',
          production_share: 2.14,
          yield_cv: 0.171,
          production_cv: 0.192,
          crop_area_concentration: 0.542,
          hhi: 0.388,
          trend: 'Stable (-0.5%)',
          scenario_exposure: 0.065
        },
        {
          district: 'Gurdaspur',
          state: 'Punjab',
          ravs: 0.561,
          classification: 'MODERATE',
          production_share: 1.95,
          yield_cv: 0.158,
          production_cv: 0.179,
          crop_area_concentration: 0.598,
          hhi: 0.445,
          trend: 'Stable (+0.1%)',
          scenario_exposure: 0.059
        },
        {
          district: 'Patiala',
          state: 'Punjab',
          ravs: 0.758,
          classification: 'VERY HIGH',
          production_share: 3.75,
          yield_cv: 0.165,
          production_cv: 0.192,
          crop_area_concentration: 0.735,
          hhi: 0.585,
          trend: 'High Concentration (+1.2%)',
          scenario_exposure: 0.115
        },
        {
          district: 'Sirsa',
          state: 'Haryana',
          ravs: 0.752,
          classification: 'VERY HIGH',
          production_share: 3.62,
          yield_cv: 0.182,
          production_cv: 0.210,
          crop_area_concentration: 0.720,
          hhi: 0.564,
          trend: 'Semi-Arid Shock Sensitivity (+3.8%)',
          scenario_exposure: 0.112
        },
        {
          district: 'Bathinda',
          state: 'Punjab',
          ravs: 0.748,
          classification: 'HIGH',
          production_share: 3.51,
          yield_cv: 0.174,
          production_cv: 0.199,
          crop_area_concentration: 0.710,
          hhi: 0.550,
          trend: 'Elevated Water Stress (+2.1%)',
          scenario_exposure: 0.108
        },
        {
          district: 'Muzaffarnagar',
          state: 'Uttar Pradesh',
          ravs: 0.672,
          classification: 'HIGH',
          production_share: 2.65,
          yield_cv: 0.205,
          production_cv: 0.231,
          crop_area_concentration: 0.605,
          hhi: 0.448,
          trend: 'Intensive Cropping (+1.5%)',
          scenario_exposure: 0.085
        },
        {
          district: 'Ganganagar',
          state: 'Rajasthan',
          ravs: 0.645,
          classification: 'HIGH',
          production_share: 2.38,
          yield_cv: 0.255,
          production_cv: 0.280,
          crop_area_concentration: 0.575,
          hhi: 0.425,
          trend: 'Canal Dependent (+4.1%)',
          scenario_exposure: 0.079
        },
        {
          district: 'Vidisha',
          state: 'Madhya Pradesh',
          ravs: 0.621,
          classification: 'HIGH',
          production_share: 2.15,
          yield_cv: 0.212,
          production_cv: 0.239,
          crop_area_concentration: 0.590,
          hhi: 0.435,
          trend: 'Dryland Vulnerability (+3.2%)',
          scenario_exposure: 0.074
        },
        {
          district: 'Kurukshetra',
          state: 'Haryana',
          ravs: 0.542,
          classification: 'MODERATE',
          production_share: 1.88,
          yield_cv: 0.160,
          production_cv: 0.181,
          crop_area_concentration: 0.525,
          hhi: 0.395,
          trend: 'Stable Diversified (-0.8%)',
          scenario_exposure: 0.056
        },
        {
          district: 'Bareilly',
          state: 'Uttar Pradesh',
          ravs: 0.528,
          classification: 'MODERATE',
          production_share: 1.72,
          yield_cv: 0.185,
          production_cv: 0.204,
          crop_area_concentration: 0.510,
          hhi: 0.380,
          trend: 'Moderate Resilience (+0.4%)',
          scenario_exposure: 0.051
        },
        {
          district: 'Kota',
          state: 'Rajasthan',
          ravs: 0.515,
          classification: 'MODERATE',
          production_share: 1.64,
          yield_cv: 0.220,
          production_cv: 0.245,
          crop_area_concentration: 0.495,
          hhi: 0.365,
          trend: 'Steady Output (+0.2%)',
          scenario_exposure: 0.048
        },
        {
          district: 'Ujjain',
          state: 'Madhya Pradesh',
          ravs: 0.492,
          classification: 'MODERATE',
          production_share: 1.55,
          yield_cv: 0.198,
          production_cv: 0.219,
          crop_area_concentration: 0.480,
          hhi: 0.355,
          trend: 'Moderate Resilience (-1.1%)',
          scenario_exposure: 0.044
        },
        {
          district: 'Patna',
          state: 'Bihar',
          ravs: 0.312,
          classification: 'LOW',
          production_share: 0.88,
          yield_cv: 0.145,
          production_cv: 0.160,
          crop_area_concentration: 0.320,
          hhi: 0.245,
          trend: 'Low Trade Exposure (0.0%)',
          scenario_exposure: 0.018
        },
        {
          district: 'Ahmedabad',
          state: 'Gujarat',
          ravs: 0.295,
          classification: 'LOW',
          production_share: 0.74,
          yield_cv: 0.138,
          production_cv: 0.152,
          crop_area_concentration: 0.305,
          hhi: 0.230,
          trend: 'Diversified Agriculture (-0.4%)',
          scenario_exposure: 0.015
        },
        {
          district: 'Pune',
          state: 'Maharashtra',
          ravs: 0.278,
          classification: 'LOW',
          production_share: 0.65,
          yield_cv: 0.132,
          production_cv: 0.148,
          crop_area_concentration: 0.285,
          hhi: 0.215,
          trend: 'Minor Producing Area (-0.2%)',
          scenario_exposure: 0.012
        },
        {
          district: 'Guntur',
          state: 'Andhra Pradesh',
          ravs: 0.245,
          classification: 'LOW',
          production_share: 0.42,
          yield_cv: 0.125,
          production_cv: 0.138,
          crop_area_concentration: 0.240,
          hhi: 0.195,
          trend: 'Peripheral Producing Zone (0.0%)',
          scenario_exposure: 0.009
        },
        {
          district: 'Belgaum',
          state: 'Karnataka',
          ravs: 0.224,
          classification: 'LOW',
          production_share: 0.35,
          yield_cv: 0.118,
          production_cv: 0.129,
          crop_area_concentration: 0.225,
          hhi: 0.180,
          trend: 'Low Vulnerability Baseline (0.0%)',
          scenario_exposure: 0.007
        },
        {
          district: 'Burdwan',
          state: 'West Bengal',
          ravs: 0.198,
          classification: 'LOW',
          production_share: 0.28,
          yield_cv: 0.110,
          production_cv: 0.122,
          crop_area_concentration: 0.210,
          hhi: 0.165,
          trend: 'Minimal Exposure (0.0%)',
          scenario_exposure: 0.005
        }
      ],
      state_scores_summary: [
        {
          state: 'Punjab',
          mean_ravs: 0.742,
          classification: 'VERY HIGH',
          n_districts: 8,
          top_district: 'Firozpur',
          max_ravs: 0.841
        },
        {
          state: 'Haryana',
          mean_ravs: 0.698,
          classification: 'HIGH',
          n_districts: 6,
          top_district: 'Karnal',
          max_ravs: 0.796
        },
        {
          state: 'Uttar Pradesh',
          mean_ravs: 0.624,
          classification: 'HIGH',
          n_districts: 12,
          top_district: 'Hardoi',
          max_ravs: 0.728
        },
        {
          state: 'Rajasthan',
          mean_ravs: 0.589,
          classification: 'HIGH',
          n_districts: 6,
          top_district: 'Baran',
          max_ravs: 0.654
        },
        {
          state: 'Madhya Pradesh',
          mean_ravs: 0.548,
          classification: 'MODERATE',
          n_districts: 8,
          top_district: 'Hoshangabad (Narmadapuram)',
          max_ravs: 0.638
        },
        {
          state: 'Bihar',
          mean_ravs: 0.284,
          classification: 'LOW',
          n_districts: 3,
          top_district: 'Patna',
          max_ravs: 0.312
        },
        {
          state: 'Gujarat',
          mean_ravs: 0.261,
          classification: 'LOW',
          n_districts: 3,
          top_district: 'Ahmedabad',
          max_ravs: 0.295
        },
        {
          state: 'Maharashtra',
          mean_ravs: 0.245,
          classification: 'LOW',
          n_districts: 3,
          top_district: 'Pune',
          max_ravs: 0.278
        },
        {
          state: 'Andhra Pradesh',
          mean_ravs: 0.218,
          classification: 'LOW',
          n_districts: 3,
          top_district: 'Guntur',
          max_ravs: 0.245
        },
        {
          state: 'Karnataka',
          mean_ravs: 0.205,
          classification: 'LOW',
          n_districts: 2,
          top_district: 'Belgaum',
          max_ravs: 0.224
        },
        {
          state: 'West Bengal',
          mean_ravs: 0.198,
          classification: 'LOW',
          n_districts: 1,
          top_district: 'Burdwan',
          max_ravs: 0.198
        }
      ],
      limitations: [
        'Vulnerability assessments are based on historical district-level agricultural datasets covering 1997–2023.',
        'The dataset does not reflect in-season weather anomalies or real-time rainfall shocks.',
        'RAVS classifications reflect structural agricultural concentration and historical yield variability.'
      ],
      disclaimer: 'Historical agricultural vulnerability index (1997-2023 baseline data). This represents structural agricultural risk, not real-time remote sensing or active season weather monitoring.'
    },
    provenance: [
      {
        source_type: '[AGRICULTURE DATA]',
        dataset: 'crop-wise-area-production-yield.csv',
        origin: 'Ministry of Agriculture and Farmers Welfare (DES)',
        time_period: '1997–1998 through 2022–2023'
      }
    ]
  },
  evidence_list: [
    {
      id: 'ev-1',
      source: 'Ministry of Agriculture and Farmers Welfare (DES)',
      source_type: 'Government Statistical Dataset',
      title: 'District-wise Crop Production Statistics (1997-2023)',
      evidence: 'Covers 320 wheat-producing districts with multi-decade acreage, production, and yield records used for RAVS baseline computation.',
      used_for: 'Vulnerability Agent — RAVS Scoring & Spatial Vulnerability',
      coverage_period: '1997-98 to 2022-23',
      provenance_tag: '[AGRICULTURE DATA]',
      citation: 'Directorate of Economics and Statistics, MoA&FW, Govt. of India'
    },
    {
      id: 'ev-2',
      source: 'Ministry of Ports, Shipping and Waterways (MoPSW)',
      source_type: 'Government Statistical Dataset',
      title: 'Basic Port Statistics of India (2023-24 & 2024-25)',
      evidence: 'Annual throughput data, major/minor port commodity shares, and berth occupancy statistics across 12 major ports.',
      used_for: 'Supply Chain Agent — Port Bottleneck & Affinity Modeling',
      coverage_period: 'FY 2023-24, FY 2024-25',
      provenance_tag: '[PORT DATA]',
      citation: 'MoPSW Transport Research Wing, Govt. of India'
    },
    {
      id: 'ev-3',
      source: 'GDELT DOC 2.0 Global News Database',
      source_type: 'GDELT News MCP',
      title: 'Geopolitical Event Ingestion & News Vector Alignment',
      evidence: 'Live journalistic mentions, Goldstein conflict-cooperation index (-4.5), and global average tone (-3.2).',
      used_for: 'Event Intelligence Agent — Context Extraction & Shock Calibration',
      coverage_period: 'Real-time 7d/30d Rolling Window',
      provenance_tag: '[GDELT DATA]',
      citation: 'Leetaru, K. & Schrodt, P. (GDELT Project)'
    },
    {
      id: 'ev-4',
      source: 'Drishti ML Econometric Cascade (Models A-D)',
      source_type: 'ML Econometric Model',
      title: 'Hierarchical Transfer Model Suite',
      evidence: 'Model A Trade Return (-4.82%), Model B Production Growth (-1.35%), Model C Wholesale Price (-2.18%), Model D Macro GVA (-0.41%).',
      used_for: 'Quantitative Impact Cascade & Propagation Engine',
      coverage_period: 'Trained on 2000-2023 Harmonized Monthly Records',
      provenance_tag: '[ML MODEL OUTPUT]',
      citation: 'Drishti Capstone Cascade Architecture'
    },
    {
      id: 'ev-5',
      source: 'NetworkX Heterogeneous MultiDiGraph Engine',
      source_type: 'MultiDiGraph Analytics',
      title: 'Supply Chain Topology & Path Propagation',
      evidence: '48 nodes, 61 weighted edges connecting partner countries, gateway ports, domestic logistics nodes, and producing states.',
      used_for: 'Supply Chain Agent — Network Centrality & Redundancy Paths',
      coverage_period: 'Topological Architecture Baseline',
      provenance_tag: '[GRAPH-DERIVED]',
      citation: 'Drishti Supply Chain Graph Builder'
    }
  ],
  llm_usage: {
    economic_interpretation: 'Gemini 2.5 Flash / Groq LLAMA-3 70B (Non-Causal Synthesis)',
    mitigation: 'Gemini 2.5 Flash / Groq LLAMA-3 70B (Action Playbook Generator)'
  }
};

export const PRESET_SCENARIOS = [
  {
    title: 'Russia stops wheat imports from India',
    query: 'Russia stopped importing wheat from India amid sanitary and trade dispute',
    commodity: 'Wheat',
    country: 'RUSSIA',
    trade_type: 'Export' as const,
    shock_intensity: 1.5,
    trade_share: 5.0,
    badge: 'Canonical Case'
  },
  {
    title: 'Black Sea grain transit disruption',
    query: 'Black Sea naval escalation disrupts grain shipping corridors and ocean bulk transport',
    commodity: 'Wheat',
    country: 'UKRAINE',
    trade_type: 'Import' as const,
    shock_intensity: 2.0,
    trade_share: 8.2,
    badge: 'Logistics Shock'
  },
  {
    title: 'Bangladesh restricts cotton import quotas',
    query: 'Bangladesh restricts raw cotton import quotas and overland rail transit from India',
    commodity: 'Cotton',
    country: 'BANGLADESH',
    trade_type: 'Export' as const,
    shock_intensity: 1.2,
    trade_share: 14.5,
    badge: 'Regional Exposure'
  }
];

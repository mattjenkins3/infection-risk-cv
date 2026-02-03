import Foundation

struct Signal: Identifiable, Codable {
    let id = UUID()
    let name: String
    let value: Double
    let weight: Double
    let note: String
}

struct RiskResponse: Codable {
    let riskScore: Double
    let riskLevel: String
    let signals: [Signal]
    let explanation: String
    let disclaimer: String
    let recommendedNextSteps: [String]

    enum CodingKeys: String, CodingKey {
        case riskScore = "risk_score"
        case riskLevel = "risk_level"
        case signals
        case explanation
        case disclaimer
        case recommendedNextSteps = "recommended_next_steps"
    }
}

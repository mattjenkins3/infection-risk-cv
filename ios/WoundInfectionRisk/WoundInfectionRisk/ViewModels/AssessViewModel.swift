import Foundation
import UIKit

@MainActor
final class AssessViewModel: ObservableObject {
    @Published var selectedImage: UIImage?
    @Published var riskResponse: RiskResponse?
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var showDisclaimer = false
    @Published var reportedPain = false
    @Published var reportedWarmth = false
    @Published var reportedSwelling = false
    @Published var reportedDrainage = false
    @Published var reportedSpreadingRedness = false

    @Published var backendURL: String {
        didSet {
            UserDefaults.standard.set(backendURL, forKey: "backendURL")
        }
    }

    private let apiService = APIService()

    init() {
        backendURL = UserDefaults.standard.string(forKey: "backendURL") ?? ""
    }

    func assessRisk() async {
        guard let image = selectedImage else {
            errorMessage = "Please select an image first."
            return
        }

        errorMessage = nil
        isLoading = true
        defer { isLoading = false }

        if backendURL.isEmpty {
            riskResponse = localDemoAssessment(image: image)
            return
        }

        do {
            let symptoms = SymptomInputs(
                reportedPain: reportedPain,
                reportedWarmth: reportedWarmth,
                reportedSwelling: reportedSwelling,
                reportedDrainage: reportedDrainage,
                reportedSpreadingRedness: reportedSpreadingRedness
            )
            riskResponse = try await apiService.assess(
                image: image,
                backendURL: backendURL,
                symptoms: symptoms
            )
        } catch {
            errorMessage = "Backend unavailable. Showing local-only demo estimate."
            riskResponse = localDemoAssessment(image: image)
        }
    }

    func testConnection() async -> Bool {
        guard !backendURL.isEmpty else {
            errorMessage = "Enter a backend URL in Settings."
            return false
        }

        do {
            let ok = try await apiService.healthCheck(backendURL: backendURL)
            if ok {
                errorMessage = nil
            }
            return ok
        } catch {
            errorMessage = "Unable to reach backend."
            return false
        }
    }

    private func localDemoAssessment(image: UIImage) -> RiskResponse {
        let score = demoScore(image: image)
        let symptomWeights: [String: Double] = [
            "reported_pain": 0.06,
            "reported_warmth": 0.08,
            "reported_swelling": 0.06,
            "reported_drainage": 0.12,
            "reported_spreading_redness": 0.1
        ]
        let symptomInputs = currentSymptoms()
        var adjustedScore = score
        var signals = [Signal(name: "local_demo", value: score, weight: 1.0, note: "Local-only heuristic signal.")]

        for (key, value) in symptomInputs {
            let weight = symptomWeights[key, default: 0.0]
            adjustedScore += weight * (value ? 1.0 : 0.0)
            signals.append(
                Signal(
                    name: key,
                    value: value ? 1.0 : 0.0,
                    weight: weight,
                    note: "User-reported symptom."
                )
            )
        }

        adjustedScore = min(max(adjustedScore, 0.0), 1.0)
        let level = adjustedScore >= 0.66 ? "high" : (adjustedScore >= 0.33 ? "medium" : "low")

        return RiskResponse(
            riskScore: adjustedScore,
            riskLevel: level,
            signals: signals,
            explanation: "Local-only demo estimate based on average color intensity. Not diagnostic.",
            disclaimer: "This output is a non-diagnostic risk estimation for triage support only.",
            recommendedNextSteps: [
                "Monitor changes over time.",
                "Seek clinical guidance if you are concerned."
            ]
        )
    }

    private func demoScore(image: UIImage) -> Double {
        guard let cgImage = image.cgImage else { return 0.0 }
        let width = cgImage.width
        let height = cgImage.height
        let bytesPerPixel = 4
        let bytesPerRow = bytesPerPixel * width
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        var rawData = [UInt8](repeating: 0, count: height * bytesPerRow)

        guard let context = CGContext(
            data: &rawData,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: bytesPerRow,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return 0.0
        }

        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))

        var redSum: Double = 0
        for i in stride(from: 0, to: rawData.count, by: 4) {
            redSum += Double(rawData[i])
        }

        let avgRed = redSum / Double(width * height) / 255.0
        return min(max(avgRed, 0.0), 1.0)
    }

    private func currentSymptoms() -> [String: Bool] {
        [
            "reported_pain": reportedPain,
            "reported_warmth": reportedWarmth,
            "reported_swelling": reportedSwelling,
            "reported_drainage": reportedDrainage,
            "reported_spreading_redness": reportedSpreadingRedness
        ]
    }
}

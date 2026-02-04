import Foundation
import UIKit

enum APIServiceError: Error {
    case invalidURL
    case invalidResponse
    case backendUnavailable
    case decodingError
    case encodingError
}

struct SymptomInputs {
    let reportedPain: Bool
    let reportedWarmth: Bool
    let reportedSwelling: Bool
    let reportedDrainage: Bool
    let reportedSpreadingRedness: Bool
}

struct APIService {
    func assess(image: UIImage, backendURL: String, symptoms: SymptomInputs) async throws -> RiskResponse {
        guard let url = URL(string: backendURL + "/assess") else {
            throw APIServiceError.invalidURL
        }

        let boundary = UUID().uuidString
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        guard let imageData = image.jpegData(compressionQuality: 0.85) else {
            throw APIServiceError.encodingError
        }

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"image.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n".data(using: .utf8)!)

        let fields: [String: Bool] = [
            "reported_pain": symptoms.reportedPain,
            "reported_warmth": symptoms.reportedWarmth,
            "reported_swelling": symptoms.reportedSwelling,
            "reported_drainage": symptoms.reportedDrainage,
            "reported_spreading_redness": symptoms.reportedSpreadingRedness
        ]

        for (key, value) in fields {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)".data(using: .utf8)!)
            body.append("\r\n".data(using: .utf8)!)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw APIServiceError.backendUnavailable
        }

        do {
            return try JSONDecoder().decode(RiskResponse.self, from: data)
        } catch {
            throw APIServiceError.decodingError
        }
    }

    func healthCheck(backendURL: String) async throws -> Bool {
        guard let url = URL(string: backendURL + "/health") else {
            throw APIServiceError.invalidURL
        }

        let (data, response) = try await URLSession.shared.data(from: url)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw APIServiceError.backendUnavailable
        }

        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        return json?["status"] as? String == "ok"
    }
}

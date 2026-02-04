import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = AssessViewModel()
    @State private var showPhotoPicker = false
    @State private var showCamera = false
    @State private var showSettings = false
    @State private var showLimitations = false

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 16) {
                    disclaimerBanner

                    imageSection

                    questionnaireSection

                    Button(action: {
                        Task { await viewModel.assessRisk() }
                    }) {
                        Text("Assess Risk")
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(10)
                    }

                    if viewModel.isLoading {
                        ProgressView("Analyzing...")
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    if let errorMessage = viewModel.errorMessage {
                        Text(errorMessage)
                            .foregroundColor(.red)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    if let result = viewModel.riskResponse {
                        ResultCard(result: result)
                    }
                }
                .padding()
            }
            .navigationTitle("Wound Risk")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Settings") { showSettings = true }
                }
            }
            .sheet(isPresented: $showPhotoPicker) {
                ImagePicker(sourceType: .photoLibrary) { image in
                    viewModel.selectedImage = image
                }
            }
            .sheet(isPresented: $showCamera) {
                ImagePicker(sourceType: .camera) { image in
                    viewModel.selectedImage = image
                }
            }
            .sheet(isPresented: $showSettings) {
                SettingsView(viewModel: viewModel)
            }
            .sheet(isPresented: $showLimitations) {
                LimitationsView()
            }
        }
    }

    private var disclaimerBanner: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Non-diagnostic risk estimation")
                .font(.headline)
            Text("This app provides triage-support risk estimates only. It does not diagnose infection or provide treatment instructions.")
                .font(.caption)
            Button("Learn more / Limitations") {
                showLimitations = true
            }
            .font(.caption)
        }
        .padding()
        .background(Color.orange.opacity(0.2))
        .cornerRadius(12)
    }

    private var imageSection: some View {
        VStack(spacing: 12) {
            if let image = viewModel.selectedImage {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(maxHeight: 240)
                    .cornerRadius(12)
            } else {
                Rectangle()
                    .fill(Color.gray.opacity(0.2))
                    .frame(height: 200)
                    .overlay(Text("No image selected"))
                    .cornerRadius(12)
            }

            HStack(spacing: 12) {
                Button("Pick Photo") { showPhotoPicker = true }
                    .buttonStyle(.bordered)
                Button("Camera") { showCamera = true }
                    .buttonStyle(.bordered)
            }
        }
    }

    private var questionnaireSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Quick questions (optional)")
                .font(.headline)
            Toggle("Is the wound painful to the touch?", isOn: $viewModel.reportedPain)
            Toggle("Is there a warm/hot feeling around the wound?", isOn: $viewModel.reportedWarmth)
            Toggle("Is there swelling around the wound?", isOn: $viewModel.reportedSwelling)
            Toggle("Is there drainage or pus?", isOn: $viewModel.reportedDrainage)
            Toggle("Is redness spreading beyond the wound edges?", isOn: $viewModel.reportedSpreadingRedness)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}

struct ResultCard: View {
    let result: RiskResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(result.riskLevel.capitalized)
                    .font(.headline)
                    .padding(8)
                    .background(badgeColor)
                    .cornerRadius(8)
                Spacer()
                Text(String(format: "%.2f", result.riskScore))
                    .font(.title2)
            }

            Text(result.explanation)
                .font(.subheadline)

            VStack(alignment: .leading, spacing: 6) {
                Text("Signals")
                    .font(.headline)
                ForEach(result.signals) { signal in
                    Text("• \(signal.name.replacingOccurrences(of: "_", with: " ")): \(String(format: "%.2f", signal.value))")
                        .font(.caption)
                }
            }

            VStack(alignment: .leading, spacing: 6) {
                Text("Recommended next steps")
                    .font(.headline)
                ForEach(result.recommendedNextSteps, id: \.self) { step in
                    Text("• \(step)")
                        .font(.caption)
                }
            }

            Text(result.disclaimer)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }

    private var badgeColor: Color {
        switch result.riskLevel {
        case "high":
            return Color.red.opacity(0.7)
        case "medium":
            return Color.orange.opacity(0.7)
        default:
            return Color.green.opacity(0.7)
        }
    }
}

struct LimitationsView: View {
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Limitations")
                        .font(.title2)
                    Text("• This tool provides non-diagnostic risk estimation only.")
                    Text("• It does not determine if a wound is infected.")
                    Text("• Lighting, camera quality, and skin tone can affect results.")
                    Text("• Always consult a clinician for medical advice.")
                }
                .padding()
            }
            .navigationTitle("Learn More")
        }
    }
}

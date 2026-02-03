import SwiftUI

struct SettingsView: View {
    @ObservedObject var viewModel: AssessViewModel
    @State private var connectionStatus: String?

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Backend")) {
                    TextField("http://192.168.1.10:8000", text: $viewModel.backendURL)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)

                    Button("Test Connection") {
                        Task {
                            let ok = await viewModel.testConnection()
                            connectionStatus = ok ? "Connected" : "Unavailable"
                        }
                    }

                    if let connectionStatus {
                        Text(connectionStatus)
                            .foregroundColor(connectionStatus == "Connected" ? .green : .red)
                    }

                    Text("Paste the LAN IP printed by the backend startup logs.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Section(header: Text("Disclaimer")) {
                    Text("This app provides non-diagnostic risk estimation only and does not provide medical advice or treatment instructions.")
                        .font(.caption)
                }
            }
            .navigationTitle("Settings")
        }
    }
}

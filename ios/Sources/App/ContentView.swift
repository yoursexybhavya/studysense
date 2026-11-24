import SwiftUI

struct ContentView: View {
    var body: some View {
        ZStack {
            Color(red: 11 / 255, green: 15 / 255, blue: 25 / 255)
                .ignoresSafeArea()
            WebView()
                .ignoresSafeArea(.keyboard)
        }
    }
}

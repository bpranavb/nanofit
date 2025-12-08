# Building the TryOn Android App

This project has been configured with **Capacitor** to allow you to build a native Android application.

## Prerequisites
1.  **Node.js** installed on your local machine.
2.  **Android Studio** installed (required for compiling the APK).

## Setup
1.  Download the code to your local machine.
2.  Install dependencies:
    ```bash
    cd frontend
    yarn install
    ```

## Building the APK
1.  Build the web assets:
    ```bash
    yarn build
    ```

2.  Sync with Android project:
    ```bash
    npx cap sync
    ```

3.  Open in Android Studio:
    ```bash
    npx cap open android
    ```
    *   This will launch Android Studio with the project loaded.
    *   Wait for Gradle sync to finish.
    *   Connect an Android device or use the Emulator.
    *   Click the **"Run"** (Play) button to install the app on the device/emulator.
    *   To build a signed APK for the Play Store, go to **Build > Generate Signed Bundle / APK**.

## PWA (Progressive Web App)
The app is also configured as a PWA. You can verify this by deploying the web app and opening it in Chrome on Android. You should see an "Install" or "Add to Home Screen" option.

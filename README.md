# Wallbreak Leads / Photo Triage Windows Build

Every push to `main` automatically runs a Windows build through GitHub Actions. The workflow creates a windowed PyInstaller application, packages it as MSIX, creates a temporary private test certificate, signs the package, and uploads the MSIX plus the matching public certificate as a workflow artifact.

## How to get the Windows app

After a push, open the repository on GitHub and click **Actions**. Select the latest **Build private Photo Triage MSIX** run. When it finishes with a green check, scroll to **Artifacts** and download `photo-triage-msix-N`, where `N` is the run number.

Extract the downloaded artifact on Windows. Open PowerShell in that folder and run:

```powershell
Import-Certificate `
  -FilePath .\PhotoTriage-TestCert.cer `
  -CertStoreLocation Cert:\CurrentUser\TrustedPeople

Add-AppxPackage .\PhotoTriage-1.0.N.0.msix
```

Replace `N` with the run number in the actual MSIX filename. The certificate is regenerated for each build, so install the matching `.cer` file from the same artifact. This is private test signing, not a public Microsoft Store certificate; SmartScreen may still show a warning.

The package requests `broadFileSystemAccess` because the app works with folders selected by the user. Windows may require enabling the app under **Settings → Privacy & security → File system**.

## Run a build manually

If you want to start a build without changing code, open **Actions**, select **Build private Photo Triage MSIX**, click **Run workflow**, choose `main`, and click the green **Run workflow** button.

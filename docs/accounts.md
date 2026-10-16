# Accounts · v0.3

## Available now

The Python deployment supports email/password registration, login, logout, seven-day server-side sessions and account-owned profile/selection/message state. A new account starts with no sample connections, no messages and no inherited demo attributes. User ID headers cannot select an account. Passwords use salted scrypt (N=32768,r=8,p=1); only hashes of random 256-bit session tokens are stored. The session cookie is HttpOnly and SameSite=Lax. HTTPS deployments set Secure, and RB_SECURE_COOKIES=1 supports TLS termination at a reverse proxy.

Auth writes and signed-in mutations require a custom header and reject unexpected browser origins. Auth attempts are limited per IP and email over ten minutes. Logout revokes the current session; expired cookies cannot silently fall back to demo state. API account state is not copied into localStorage. Responses from a previous account scope are discarded when switching accounts.

Accounts currently interact with fictional sample profiles. This is not a released dating network. Email delivery/verification, password recovery, account deletion, moderation and a directory of consenting real members remain release work.

## Google configuration

The web integration uses Google Identity Services, a short-lived one-use nonce and server-side google-auth ID-token verification. The verifier checks the signature, audience, issuer and expiry; the application checks nonce and verified email, and identifies returning users by Google's sub. It does not silently link an existing password account by matching its email.

1. In a Google Cloud account, create/select a project and configure Google Auth Platform branding/audience. Configure only basic identity scopes: openid, email and profile.
2. Create an OAuth client of type Web application. Add exact authorized JavaScript origins, such as http://localhost:8000 and http://127.0.0.1:8000 for development, and the eventual HTTPS Python deployment origin. No client secret is needed for this ID-token flow.
3. Set RB_GOOGLE_CLIENT_ID to the public client ID on the Python server and restart it. Do not place an invented ID in the client bundle. The status endpoint supplies the configured public ID to the UI.
4. Complete a real Google sign-in with a test user before enabling this for other users. The current automated tests mock the verifier boundary; they do not claim a live Google authentication test.

Source: https://developers.google.com/identity/gsi/web/guides/verify-google-id-token and https://developers.google.com/identity/gsi/web/reference/js-reference.

The Cloud console returned HTTP 403 in this environment, so no Google Cloud project/client was created. Without a client ID, the UI explicitly shows Google sign-in as pending and the endpoint rejects attempts with 503.

## Hosting boundaries

The existing Sites publication is a private static design preview. Its platform sign-in/access policy is preserved. It does not run Python or store application accounts, and the account screen explicitly says account creation is unavailable there. The bundled Android/iOS sample also remains offline demo mode. This does not pretend that browser-local sample state is authentication.

To make account creation available on a public application, deploy Angular's dist and the Python API on an HTTPS Python host under the same origin, with persistent database storage and RB_SECURE_COOKIES=1. Add the actual origin to the Google OAuth client. The source is ready for that deployment, but no external Python hosting account or domain is connected in this task. Native Google login needs a platform-appropriate external-browser/native identity flow before store release; it has not been tested in a device WebView.

## Local setup

Install backend/requirements.lock.txt and run python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 from the project root. Environment variable names are documented in backend/.env.example; this file is a reference and is not auto-loaded. On PowerShell, set $env:RB_GOOGLE_CLIENT_ID='your-public-client-id' before the Uvicorn command.

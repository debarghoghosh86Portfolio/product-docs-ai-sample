# Account and security

## Reset your password

If you forgot your password:

1. On the login page, click **Forgot password?**.
2. Enter the email address you signed up with.
3. Open the reset email and click **Reset password**. The reset link is valid for 30 minutes and can only be used once.
4. Choose a new password. You cannot reuse any of your last 5 passwords.

After a password reset, TaskFlow signs you out of all other devices.

If you don't receive the email within 5 minutes, check your spam folder or ask your workspace admin to send a reset link from **Settings > Members**.

## Two-factor authentication (2FA)

TaskFlow supports 2FA with authenticator apps such as Google Authenticator, Microsoft Authenticator, or 1Password. SMS codes are not supported.

To turn on 2FA, go to **Profile > Security > Two-factor authentication**, scan the QR code with your authenticator app, and enter the 6-digit code. Save your 10 backup codes in a safe place; each backup code works once.

Workspace admins on the Business plan can require 2FA for all members from **Settings > Security**.

## Single sign-on (SSO)

SSO with SAML 2.0 (Okta, Azure AD / Entra ID, Google Workspace) is available on the Business plan only. Admins configure it under **Settings > Security > SSO**. When SSO is enforced, members can no longer sign in with a password.

## Sessions

Sessions expire after 30 days of inactivity. You can see and sign out of active sessions from **Profile > Security > Active sessions**.

import { initializeApp, getApps, getApp } from 'firebase/app';
import {
  getAuth,
  GoogleAuthProvider,
  GithubAuthProvider,
  signInWithPopup,
  signOut as fbSignOut,
  User
} from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyB7t6zRal6bW4jzOOZpTjq4lZc-lkoGFp0",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "www.brandonfoster.dev",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "portfolio-510722",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "portfolio-510722.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "339039725614",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:339039725614:web:cf9958d6fe4be5d12017bf"
};

const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
export const auth = getAuth(app);

const googleProvider = new GoogleAuthProvider();
const githubProvider = new GithubAuthProvider();

export function loginAsDevDemo(role: 'recruiter' | 'engineer' = 'recruiter'): { token: string; user: User } {
  if (role === 'engineer') {
    return {
      token: "dev-test-token-github-engineer",
      user: {
        uid: "github-engineer-uid",
        displayName: "Senior Engineer",
        email: "engineer@github-community.org",
        photoURL: null,
      } as unknown as User
    };
  }
  return {
    token: "dev-test-token-recruiter-demo",
    user: {
      uid: "recruiter-demo-uid",
      displayName: "Technical Recruiter",
      email: "recruiter@hiringtech.com",
      photoURL: null,
    } as unknown as User
  };
}

export async function loginWithGoogle(): Promise<{ token: string; user: User | null }> {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const token = await result.user.getIdToken();
    return { token, user: result.user };
  } catch (error: any) {
    if (error?.code === 'auth/popup-closed-by-user' || error?.code === 'auth/cancelled-popup-request') {
      throw new Error('Sign-in cancelled. Popup was closed before completion.');
    }

    if (import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH_BYPASS === 'true') {
      console.warn("Dev mode fallback: using simulated token:", error);
      return loginAsDevDemo('recruiter');
    }

    console.error("Firebase Google popup error:", error);
    let message = error?.message || "Google authentication failed";
    if (error?.code === 'auth/operation-not-allowed') {
      message = "Google Sign-In is not enabled yet in the Firebase Console (Authentication > Sign-in method).";
    } else if (error?.code === 'auth/unauthorized-domain') {
      message = "This domain is not authorized in Firebase Console (Authentication > Settings > Authorized domains).";
    } else if (error?.code === 'auth/api-key-not-valid') {
      message = "Firebase API key is invalid or restricted. Please verify Firebase project settings.";
    }
    throw new Error(message);
  }
}

export async function loginWithGithub(): Promise<{ token: string; user: User | null }> {
  try {
    const result = await signInWithPopup(auth, githubProvider);
    const token = await result.user.getIdToken();
    return { token, user: result.user };
  } catch (error: any) {
    if (error?.code === 'auth/popup-closed-by-user' || error?.code === 'auth/cancelled-popup-request') {
      throw new Error('Sign-in cancelled. Popup was closed before completion.');
    }

    if (import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH_BYPASS === 'true') {
      console.warn("Dev mode fallback: using simulated token:", error);
      return loginAsDevDemo('engineer');
    }

    console.error("Firebase GitHub popup error:", error);
    let message = error?.message || "GitHub authentication failed";
    if (error?.code === 'auth/operation-not-allowed') {
      message = "GitHub Sign-In is not enabled yet in the Firebase Console (Authentication > Sign-in method).";
    } else if (error?.code === 'auth/unauthorized-domain') {
      message = "This domain is not authorized in Firebase Console (Authentication > Settings > Authorized domains).";
    }
    throw new Error(message);
  }
}

export async function logout(): Promise<void> {
  try {
    await fbSignOut(auth);
  } catch (e) {
    console.log("Logged out");
  }
}

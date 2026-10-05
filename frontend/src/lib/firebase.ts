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
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyDummyKeyForTestingAndDemoMode",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "portfolio-demo.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "portfolio-demo",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "portfolio-demo.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "1234567890",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:1234567890:web:abcdef"
};

const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
export const auth = getAuth(app);

const googleProvider = new GoogleAuthProvider();
const githubProvider = new GithubAuthProvider();

export async function loginWithGoogle(): Promise<{ token: string; user: User | null }> {
  try {
    const result = await signInWithPopup(auth, googleProvider);
    const token = await result.user.getIdToken();
    return { token, user: result.user };
  } catch (error) {
    console.warn("Firebase popup failed or not configured, using simulated dev auth token:", error);
    // Development fallback token accepted by backend dev mode
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
}

export async function loginWithGithub(): Promise<{ token: string; user: User | null }> {
  try {
    const result = await signInWithPopup(auth, githubProvider);
    const token = await result.user.getIdToken();
    return { token, user: result.user };
  } catch (error) {
    console.warn("Firebase GitHub popup fallback:", error);
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
}

export async function logout(): Promise<void> {
  try {
    await fbSignOut(auth);
  } catch (e) {
    console.log("Logged out");
  }
}

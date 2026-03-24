import { useEffect, useRef, useState } from 'react';

import authService from '../services/authService';


const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;


function GoogleSignInButton({ onSuccess, onError }) {
  const containerRef = useRef(null);
  const [scriptLoaded, setScriptLoaded] = useState(() => Boolean(window.google?.accounts?.id));

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      return undefined;
    }

    if (window.google?.accounts?.id) {
      return undefined;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setScriptLoaded(true);
    script.onerror = () => onError?.(new Error('Failed to load Google Sign-In.'));
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [onError]);

  useEffect(() => {
    if (!scriptLoaded || !containerRef.current || !window.google?.accounts?.id || !GOOGLE_CLIENT_ID) {
      return;
    }

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: async (response) => {
        try {
          const user = await authService.loginWithGoogle({ id_token: response.credential });
          onSuccess?.(user);
        } catch (error) {
          onError?.(error);
        }
      },
    });

    containerRef.current.innerHTML = '';
    window.google.accounts.id.renderButton(containerRef.current, {
      theme: 'outline',
      size: 'large',
      text: 'continue_with',
      shape: 'pill',
      width: 320,
    });
  }, [onError, onSuccess, scriptLoaded]);

  if (!GOOGLE_CLIENT_ID) {
    return null;
  }

  return <div ref={containerRef} className="flex justify-center" />;
}


export default GoogleSignInButton;

import { useState, useEffect } from 'react';
import { supabase, User, AuthSession } from '../utils/supabase';
import { Session } from '@supabase/supabase-js';

export interface AuthState {
  user: User | null;
  session: Session | null;
  loading: boolean;
  error: string | null;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    session: null,
    loading: true,
    error: null
  });

  useEffect(() => {
    // 초기 세션 확인
    const getInitialSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('세션 확인 오류:', error);
          setAuthState(prev => ({ ...prev, error: error.message, loading: false }));
          return;
        }

        setAuthState({
          user: session?.user as User || null,
          session,
          loading: false,
          error: null
        });
      } catch (error) {
        console.error('초기 세션 확인 실패:', error);
        setAuthState(prev => ({ 
          ...prev, 
          error: '인증 상태 확인에 실패했습니다.', 
          loading: false 
        }));
      }
    };

    getInitialSession();

    // 인증 상태 변경 감지
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Auth state changed:', event, session?.user?.email);
        
        setAuthState({
          user: session?.user as User || null,
          session,
          loading: false,
          error: null
        });

        // 로그인 성공 시 추가 처리
        if (event === 'SIGNED_IN' && session?.user) {
          console.log('사용자 로그인 성공:', session.user.email);
        }

        // 로그아웃 시 추가 처리
        if (event === 'SIGNED_OUT') {
          console.log('사용자 로그아웃');
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Google 로그인
  const signInWithGoogle = async () => {
    try {
      setAuthState(prev => ({ ...prev, loading: true, error: null }));
      
      // 환경 변수 기반 리다이렉트 URL 구성 (미설정 시 현재 origin 사용)
      const siteUrl = (import.meta.env.VITE_SITE_URL || window.location.origin).replace(/\/$/, '');
      const redirectUrl = `${siteUrl}/auth/callback`;

      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: redirectUrl
        }
      });

      if (error) {
        throw error;
      }

      return { data, error: null };
    } catch (error: any) {
      console.error('Google 로그인 오류:', error);
      setAuthState(prev => ({ 
        ...prev, 
        error: error.message || 'Google 로그인에 실패했습니다.',
        loading: false 
      }));
      return { data: null, error: error.message };
    }
  };



  // 로그아웃
  const signOut = async () => {
    try {
      setAuthState(prev => ({ ...prev, loading: true, error: null }));
      
      const { error } = await supabase.auth.signOut();
      
      if (error) {
        throw error;
      }

      return { error: null };
    } catch (error: any) {
      console.error('로그아웃 오류:', error);
      setAuthState(prev => ({ 
        ...prev, 
        error: error.message || '로그아웃에 실패했습니다.',
        loading: false 
      }));
      return { error: error.message };
    }
  };

  return {
    ...authState,
    signInWithGoogle,
    signOut
  };
};
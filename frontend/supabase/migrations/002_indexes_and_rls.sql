-- Popular-77 프로젝트 인덱스 및 RLS 정책
-- 생성일: 2024-12-30
-- 설명: 성능 최적화를 위한 인덱스와 보안을 위한 RLS 정책 설정

-- ============================================
-- 인덱스 생성 (성능 최적화)
-- ============================================

-- user_profiles 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_profiles_created_at ON public.user_profiles(created_at);
CREATE INDEX IF NOT EXISTS idx_user_profiles_provider ON public.user_profiles(provider);
CREATE INDEX IF NOT EXISTS idx_user_profiles_is_premium ON public.user_profiles(is_premium);

-- conversion_history 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_conversion_history_user_id ON public.conversion_history(user_id);
CREATE INDEX IF NOT EXISTS idx_conversion_history_session_id ON public.conversion_history(session_id);
CREATE INDEX IF NOT EXISTS idx_conversion_history_status ON public.conversion_history(status);
CREATE INDEX IF NOT EXISTS idx_conversion_history_conversion_type ON public.conversion_history(conversion_type);
CREATE INDEX IF NOT EXISTS idx_conversion_history_created_at ON public.conversion_history(created_at);
CREATE INDEX IF NOT EXISTS idx_conversion_history_completed_at ON public.conversion_history(completed_at);

-- user_files 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON public.user_files(user_id);
CREATE INDEX IF NOT EXISTS idx_user_files_session_id ON public.user_files(session_id);
CREATE INDEX IF NOT EXISTS idx_user_files_expires_at ON public.user_files(expires_at);
CREATE INDEX IF NOT EXISTS idx_user_files_file_hash ON public.user_files(file_hash);
CREATE INDEX IF NOT EXISTS idx_user_files_is_temporary ON public.user_files(is_temporary);

-- daily_analytics 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON public.daily_analytics(date);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_conversion_type ON public.daily_analytics(conversion_type);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_date_type ON public.daily_analytics(date, conversion_type);

-- api_usage 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_api_usage_user_id ON public.api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON public.api_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON public.api_usage(endpoint);

-- user_feedback 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_user_feedback_status ON public.user_feedback(status);
CREATE INDEX IF NOT EXISTS idx_user_feedback_category ON public.user_feedback(category);
CREATE INDEX IF NOT EXISTS idx_user_feedback_created_at ON public.user_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_user_feedback_user_id ON public.user_feedback(user_id);

-- ============================================
-- RLS (Row Level Security) 정책 설정
-- ============================================

-- RLS 활성화
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversion_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_feedback ENABLE ROW LEVEL SECURITY;
-- daily_analytics는 관리자만 접근하므로 RLS 비활성화

-- user_profiles 정책
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- conversion_history 정책
CREATE POLICY "Users can view own conversion history" ON public.conversion_history
    FOR SELECT USING (
        auth.uid() = user_id OR 
        (user_id IS NULL AND session_id IS NOT NULL)
    );

CREATE POLICY "Users can insert own conversion history" ON public.conversion_history
    FOR INSERT WITH CHECK (
        auth.uid() = user_id OR 
        (user_id IS NULL AND session_id IS NOT NULL)
    );

CREATE POLICY "Users can update own conversion history" ON public.conversion_history
    FOR UPDATE USING (
        auth.uid() = user_id OR 
        (user_id IS NULL AND session_id IS NOT NULL)
    );

-- user_files 정책
CREATE POLICY "Users can view own files" ON public.user_files
    FOR SELECT USING (
        auth.uid() = user_id OR 
        (user_id IS NULL AND session_id IS NOT NULL)
    );

CREATE POLICY "Users can insert own files" ON public.user_files
    FOR INSERT WITH CHECK (
        auth.uid() = user_id OR 
        (user_id IS NULL AND session_id IS NOT NULL)
    );

CREATE POLICY "Users can update own files" ON public.user_files
    FOR UPDATE USING (
        auth.uid() = user_id OR 
        (user_id IS NULL AND session_id IS NOT NULL)
    );

CREATE POLICY "Users can delete own files" ON public.user_files
    FOR DELETE USING (
        auth.uid() = user_id OR 
        (user_id IS NULL AND session_id IS NOT NULL)
    );

-- user_settings 정책
CREATE POLICY "Users can view own settings" ON public.user_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own settings" ON public.user_settings
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own settings" ON public.user_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- api_usage 정책
CREATE POLICY "Users can view own API usage" ON public.api_usage
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service can insert API usage" ON public.api_usage
    FOR INSERT WITH CHECK (true); -- 서비스에서 삽입 가능

-- user_feedback 정책
CREATE POLICY "Users can view own feedback" ON public.user_feedback
    FOR SELECT USING (
        auth.uid() = user_id OR 
        user_id IS NULL
    );

CREATE POLICY "Anyone can insert feedback" ON public.user_feedback
    FOR INSERT WITH CHECK (true); -- 누구나 피드백 제출 가능

CREATE POLICY "Users can update own feedback" ON public.user_feedback
    FOR UPDATE USING (auth.uid() = user_id);
-- Popular-77 프로젝트 초기 데이터베이스 스키마
-- 생성일: 2024-12-30
-- 설명: 사용자 인증, 파일 변환 기록, 사용 통계를 위한 테이블 생성

-- 1. 사용자 프로필 테이블 (Supabase Auth와 연동)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    provider TEXT, -- 'google', 'kakao' 등
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_premium BOOLEAN DEFAULT FALSE,
    total_conversions INTEGER DEFAULT 0,
    monthly_conversions INTEGER DEFAULT 0,
    monthly_reset_date DATE DEFAULT CURRENT_DATE
);

-- 2. 파일 변환 기록 테이블
CREATE TABLE IF NOT EXISTS public.conversion_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    session_id TEXT, -- 비로그인 사용자를 위한 세션 ID
    original_filename TEXT NOT NULL,
    original_file_size BIGINT NOT NULL,
    original_format TEXT NOT NULL,
    target_format TEXT NOT NULL,
    conversion_type TEXT NOT NULL, -- 'pdf-to-jpg', 'pdf-to-doc', 'image-resize' 등
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed', 'cancelled')),
    processing_time_ms INTEGER,
    output_filename TEXT,
    output_file_size BIGINT,
    error_message TEXT,
    conversion_options JSONB, -- 품질, 크기, 투명도 등 변환 옵션
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- 3. 사용자 파일 정보 테이블 (업로드된 파일 메타데이터)
CREATE TABLE IF NOT EXISTS public.user_files (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    session_id TEXT, -- 비로그인 사용자용
    filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT,
    file_hash TEXT, -- 중복 파일 체크용
    storage_path TEXT, -- 실제 저장 경로 (임시)
    is_temporary BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 일일 사용 통계 테이블
CREATE TABLE IF NOT EXISTS public.daily_analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    date DATE NOT NULL,
    conversion_type TEXT NOT NULL,
    total_conversions INTEGER DEFAULT 0,
    successful_conversions INTEGER DEFAULT 0,
    failed_conversions INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    unique_sessions INTEGER DEFAULT 0,
    total_file_size BIGINT DEFAULT 0,
    avg_processing_time_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(date, conversion_type)
);

-- 5. 사용자 설정 테이블
CREATE TABLE IF NOT EXISTS public.user_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE UNIQUE,
    default_quality TEXT DEFAULT 'high',
    auto_download BOOLEAN DEFAULT TRUE,
    email_notifications BOOLEAN DEFAULT FALSE,
    language TEXT DEFAULT 'ko',
    theme TEXT DEFAULT 'light',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. API 사용량 추적 테이블 (향후 API 서비스용)
CREATE TABLE IF NOT EXISTS public.api_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    api_key_id TEXT,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    request_size BIGINT,
    response_size BIGINT,
    processing_time_ms INTEGER,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. 피드백 및 문의 테이블
CREATE TABLE IF NOT EXISTS public.user_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE SET NULL,
    email TEXT,
    name TEXT,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT DEFAULT 'general' CHECK (category IN ('general', 'bug', 'feature', 'support')),
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
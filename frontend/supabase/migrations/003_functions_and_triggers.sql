-- Popular-77 프로젝트 함수 및 트리거
-- 생성일: 2024-12-30
-- 설명: 자동화된 데이터 처리를 위한 함수와 트리거

-- ============================================
-- 트리거 함수들
-- ============================================

-- updated_at 자동 업데이트 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- updated_at 트리거 적용
CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON public.user_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_analytics_updated_at 
    BEFORE UPDATE ON public.daily_analytics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_settings_updated_at 
    BEFORE UPDATE ON public.user_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_feedback_updated_at 
    BEFORE UPDATE ON public.user_feedback 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 사용자 프로필 자동 생성 함수
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, display_name, avatar_url, provider, last_login_at)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'avatar_url',
        NEW.raw_app_meta_data->>'provider',
        NOW()
    )
    ON CONFLICT (id) DO UPDATE SET
        last_login_at = NOW(),
        display_name = COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', user_profiles.display_name),
        avatar_url = COALESCE(NEW.raw_user_meta_data->>'avatar_url', user_profiles.avatar_url);
    
    -- 기본 설정 생성
    INSERT INTO public.user_settings (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 사용자 생성/로그인 시 프로필 자동 생성 트리거
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT OR UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- 유틸리티 함수들
-- ============================================

-- 만료된 임시 파일 정리 함수
CREATE OR REPLACE FUNCTION public.cleanup_expired_files()
RETURNS void AS $$
BEGIN
    DELETE FROM public.user_files 
    WHERE is_temporary = TRUE 
    AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 월별 변환 횟수 리셋 함수
CREATE OR REPLACE FUNCTION public.reset_monthly_conversions()
RETURNS void AS $$
BEGIN
    UPDATE public.user_profiles 
    SET 
        monthly_conversions = 0,
        monthly_reset_date = CURRENT_DATE
    WHERE monthly_reset_date < CURRENT_DATE - INTERVAL '1 month';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 사용자 통계 업데이트 함수
CREATE OR REPLACE FUNCTION public.update_user_conversion_stats(
    p_user_id UUID,
    p_session_id TEXT DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    IF p_user_id IS NOT NULL THEN
        UPDATE public.user_profiles 
        SET 
            total_conversions = total_conversions + 1,
            monthly_conversions = monthly_conversions + 1
        WHERE id = p_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 일일 통계 업데이트 함수
CREATE OR REPLACE FUNCTION public.update_daily_analytics(
    p_conversion_type TEXT,
    p_success BOOLEAN,
    p_processing_time_ms INTEGER DEFAULT NULL,
    p_file_size BIGINT DEFAULT NULL,
    p_user_id UUID DEFAULT NULL,
    p_session_id TEXT DEFAULT NULL
)
RETURNS void AS $$
DECLARE
    today_date DATE := CURRENT_DATE;
BEGIN
    INSERT INTO public.daily_analytics (
        date, 
        conversion_type, 
        total_conversions,
        successful_conversions,
        failed_conversions,
        unique_users,
        unique_sessions,
        total_file_size,
        avg_processing_time_ms
    )
    VALUES (
        today_date,
        p_conversion_type,
        1,
        CASE WHEN p_success THEN 1 ELSE 0 END,
        CASE WHEN p_success THEN 0 ELSE 1 END,
        CASE WHEN p_user_id IS NOT NULL THEN 1 ELSE 0 END,
        CASE WHEN p_session_id IS NOT NULL THEN 1 ELSE 0 END,
        COALESCE(p_file_size, 0),
        COALESCE(p_processing_time_ms, 0)
    )
    ON CONFLICT (date, conversion_type) DO UPDATE SET
        total_conversions = daily_analytics.total_conversions + 1,
        successful_conversions = daily_analytics.successful_conversions + CASE WHEN p_success THEN 1 ELSE 0 END,
        failed_conversions = daily_analytics.failed_conversions + CASE WHEN p_success THEN 0 ELSE 1 END,
        total_file_size = daily_analytics.total_file_size + COALESCE(p_file_size, 0),
        avg_processing_time_ms = CASE 
            WHEN p_processing_time_ms IS NOT NULL THEN 
                (daily_analytics.avg_processing_time_ms * (daily_analytics.total_conversions - 1) + p_processing_time_ms) / daily_analytics.total_conversions
            ELSE daily_analytics.avg_processing_time_ms
        END,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
/** 
 * 파일 다운로드 유틸리티 함수들
 * RFC 6266 표준을 지원하여 한글 등 다국어 파일명이 깨지는 것을 방지합니다.
 */

/** 
 * HTTP 응답 헤더(content-disposition)에서 파일명을 추출하는 함수입니다. 
 * RFC 6266 표준(UTF-8)을 우선적으로 처리하여 한글 등 다국어 파일명이 깨지는 것을 방지합니다. 
 * 
 * @param {Response} response - fetch API의 응답(response) 객체입니다. 
 * @param {string} defaultFilename - 파일명을 찾지 못했을 때 사용할 기본 파일명입니다. 
 * @returns {string} 추출된 파일명 또는 기본 파일명을 반환합니다. 
 */ 
function getFilenameFromHeader(response, defaultFilename = 'downloaded_file') { 
    const contentDisposition = response.headers.get('content-disposition'); 
    let filename = defaultFilename; // 기본값 설정 

    if (contentDisposition) { 
        // 표준 방식 (RFC 6266): filename*=UTF-8''... (한글 등 다국어 지원) 
        const utf8FilenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/); 
        if (utf8FilenameMatch && utf8FilenameMatch[1]) { 
            // URI 인코딩된 문자열을 디코딩하여 원본 파일명으로 복원합니다. 
            filename = decodeURIComponent(utf8FilenameMatch[1]); 
        } else { 
            // 구형 또는 비표준 방식: filename="..." 
            const plainFilenameMatch = contentDisposition.match(/filename="(.+)"/); 
            if (plainFilenameMatch && plainFilenameMatch[1]) { 
                // 이 방식은 서버 인코딩에 따라 한글이 깨질 수 있습니다. 
                filename = plainFilenameMatch[1]; 
            } 
        } 
    } 
    return filename; 
}

/** 
 * 서버로부터 파일을 다운로드하고 저장하는 메인 함수 
 * @param {string} url - 파일을 요청할 API 주소 
 * @param {string} defaultFilename - 다운로드 실패 또는 파일명 부재 시 사용할 이름 
 * @param {Object} options - fetch 옵션 (method, body, headers 등)
 * @param {HTMLElement} statusElement - 상태를 표시할 DOM 요소 (선택사항)
 * @returns {Promise<string>} 다운로드된 파일명을 반환하는 Promise
 */ 
function downloadFile(url, defaultFilename, options = {}, statusElement = null) { 
    const fetchOptions = {
        method: 'GET',
        ...options
    };
    
    // 상태 표시 함수
    const updateStatus = (message, className = 'alert alert-info mt-3') => {
        if (statusElement) {
            statusElement.className = className;
            statusElement.innerHTML = message;
            statusElement.style.display = 'block';
        }
    };
    
    updateStatus('파일 변환 및 다운로드를 시작합니다...');

    return fetch(url, fetchOptions) 
        .then(response => { 
            if (!response.ok) { 
                // 서버에서 오류 응답이 온 경우 
                throw new Error(`서버 오류: ${response.status} ${response.statusText}`); 
            } 

            // 1. 위에서 만든 함수를 호출하여 파일명을 간단하게 추출합니다. 
            const filename = getFilenameFromHeader(response, defaultFilename); 

            // 2. UI에 변환 완료 및 파일명 표시 
            updateStatus(`변환 완료! <strong>${filename}</strong> 파일이 다운로드됩니다.`, 'alert alert-success mt-3');

            // 3. 응답 본문(blob)을 받아 파일 다운로드 처리 
            return response.blob().then(blob => ({ filename, blob })); 
        }) 
        .then(({ filename, blob }) => { 
            // 다운로드를 위한 임시 링크 생성 
            const link = document.createElement('a'); 
            link.href = URL.createObjectURL(blob); 
            link.download = filename; // 추출한 파일명을 여기에 설정 

            // 링크를 문서에 추가하고 클릭 이벤트를 발생시켜 다운로드 실행 
            document.body.appendChild(link); 
            link.click(); 

            // 사용이 끝난 임시 링크와 URL 객체 정리 
            document.body.removeChild(link); 
            URL.revokeObjectURL(link.href); 
            
            return filename;
        }) 
        .catch(error => { 
            // 네트워크 오류 또는 기타 예외 처리 
            console.error('다운로드 중 오류 발생:', error); 
            updateStatus(`오류가 발생했습니다: ${error.message}`, 'alert alert-danger mt-3');
            throw error; 
        }); 
}

/**
 * 간단한 파일 다운로드 함수 (상태 표시 없음)
 * @param {string} url - 다운로드할 파일의 URL
 * @param {string} filename - 저장할 파일명
 */
function simpleDownload(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Blob 데이터를 파일로 다운로드하는 함수
 * @param {Blob} blob - 다운로드할 Blob 데이터
 * @param {string} filename - 저장할 파일명
 */
function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    simpleDownload(url, filename);
    URL.revokeObjectURL(url);
}

// 전역 스코프에 함수들을 노출 (모듈 시스템을 사용하지 않는 경우)
if (typeof window !== 'undefined') {
    window.getFilenameFromHeader = getFilenameFromHeader;
    window.downloadFile = downloadFile;
    window.simpleDownload = simpleDownload;
    window.downloadBlob = downloadBlob;
}

// CommonJS 모듈 지원
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getFilenameFromHeader,
        downloadFile,
        simpleDownload,
        downloadBlob
    };
}

// ES6 모듈 지원 (모듈 환경에서만 사용)
// export는 모듈 스크립트에서만 사용 가능하므로 주석 처리
/*
export {
    getFilenameFromHeader,
    downloadFile,
    simpleDownload,
    downloadBlob
};
*/
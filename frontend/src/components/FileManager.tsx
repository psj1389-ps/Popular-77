import React, { useState, useCallback } from 'react';
import { Upload, File, Folder, Download, Trash2, Eye, Search, Filter, Grid, List, MoreVertical } from 'lucide-react';

interface FileItem {
  id: string;
  name: string;
  type: 'file' | 'folder';
  size?: number;
  modified: Date;
  status?: 'uploading' | 'processing' | 'completed' | 'error';
  progress?: number;
  thumbnail?: string;
}

interface FileManagerProps {
  onFileSelect?: (file: FileItem) => void;
  onFileUpload?: (files: FileList) => void;
  allowMultiple?: boolean;
  acceptedTypes?: string[];
}

const FileManager: React.FC<FileManagerProps> = ({
  onFileSelect,
  onFileUpload,
  allowMultiple = true,
  acceptedTypes = ['video/*', 'audio/*', 'image/*']
}) => {
  const [files, setFiles] = useState<FileItem[]>([
    {
      id: '1',
      name: 'sample-video.mp4',
      type: 'file',
      size: 15728640, // 15MB
      modified: new Date('2024-01-15'),
      status: 'completed'
    },
    {
      id: '2',
      name: 'audio-track.mp3',
      type: 'file',
      size: 5242880, // 5MB
      modified: new Date('2024-01-14'),
      status: 'completed'
    },
    {
      id: '3',
      name: 'Documents',
      type: 'folder',
      modified: new Date('2024-01-13')
    },
    {
      id: '4',
      name: 'converting-video.avi',
      type: 'file',
      size: 25165824, // 24MB
      modified: new Date('2024-01-16'),
      status: 'processing',
      progress: 65
    }
  ]);

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [dragOver, setDragOver] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0 && onFileUpload) {
      onFileUpload(droppedFiles);
    }
  }, [onFileUpload]);

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0 && onFileUpload) {
      onFileUpload(selectedFiles);
    }
  };

  const handleFileSelect = (fileId: string) => {
    if (allowMultiple) {
      setSelectedFiles(prev => 
        prev.includes(fileId) 
          ? prev.filter(id => id !== fileId)
          : [...prev, fileId]
      );
    } else {
      setSelectedFiles([fileId]);
      const file = files.find(f => f.id === fileId);
      if (file && onFileSelect) {
        onFileSelect(file);
      }
    }
  };

  const handleDelete = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    setSelectedFiles(prev => prev.filter(id => id !== fileId));
  };

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'uploading': return 'text-blue-600';
      case 'processing': return 'text-yellow-600';
      case 'completed': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'uploading': return '업로드 중';
      case 'processing': return '처리 중';
      case 'completed': return '완료';
      case 'error': return '오류';
      default: return '';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* 헤더 */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">파일 관리</h2>
          <div className="flex items-center space-x-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="파일 검색..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="flex items-center border border-gray-300 rounded-md">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 ${viewMode === 'grid' ? 'bg-blue-50 text-blue-600' : 'text-gray-400'}`}
              >
                <Grid className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 ${viewMode === 'list' ? 'bg-blue-50 text-blue-600' : 'text-gray-400'}`}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 업로드 영역 */}
      <div
        className={`mx-6 mt-4 border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragOver 
            ? 'border-blue-400 bg-blue-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <div className="text-lg font-medium text-gray-900 mb-2">
          파일을 드래그하여 업로드하거나 클릭하세요
        </div>
        <p className="text-sm text-gray-500 mb-4">
          지원 형식: 비디오, 오디오, 이미지 파일
        </p>
        <input
          type="file"
          multiple={allowMultiple}
          accept={acceptedTypes.join(',')}
          onChange={handleFileInputChange}
          className="hidden"
          id="file-upload"
        />
        <label
          htmlFor="file-upload"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
        >
          <Upload className="h-4 w-4 mr-2" />
          파일 선택
        </label>
      </div>

      {/* 파일 목록 */}
      <div className="p-6">
        {filteredFiles.length === 0 ? (
          <div className="text-center py-12">
            <File className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500">파일이 없습니다</p>
          </div>
        ) : (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4' : 'space-y-2'}>
            {filteredFiles.map((file) => (
              <div
                key={file.id}
                className={`${
                  viewMode === 'grid'
                    ? 'border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer'
                    : 'flex items-center justify-between p-3 hover:bg-gray-50 rounded-md cursor-pointer'
                } ${selectedFiles.includes(file.id) ? 'ring-2 ring-blue-500 bg-blue-50' : ''}`}
                onClick={() => handleFileSelect(file.id)}
              >
                {viewMode === 'grid' ? (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        {file.type === 'folder' ? (
                          <Folder className="h-8 w-8 text-blue-500" />
                        ) : (
                          <File className="h-8 w-8 text-gray-400" />
                        )}
                      </div>
                      <div className="relative">
                        <button className="p-1 hover:bg-gray-100 rounded">
                          <MoreVertical className="h-4 w-4 text-gray-400" />
                        </button>
                      </div>
                    </div>
                    <div className="mb-2">
                      <h3 className="text-sm font-medium text-gray-900 truncate" title={file.name}>
                        {file.name}
                      </h3>
                      {file.size && (
                        <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                      )}
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{formatDate(file.modified)}</span>
                      {file.status && (
                        <span className={getStatusColor(file.status)}>
                          {getStatusText(file.status)}
                        </span>
                      )}
                    </div>
                    {file.status === 'processing' && file.progress && (
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div 
                            className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${file.progress}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">{file.progress}%</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <>
                    <div className="flex items-center flex-1 min-w-0">
                      {file.type === 'folder' ? (
                        <Folder className="h-5 w-5 text-blue-500 mr-3 flex-shrink-0" />
                      ) : (
                        <File className="h-5 w-5 text-gray-400 mr-3 flex-shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>{formatDate(file.modified)}</span>
                          {file.size && <span>{formatFileSize(file.size)}</span>}
                          {file.status && (
                            <span className={getStatusColor(file.status)}>
                              {getStatusText(file.status)}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {file.status === 'processing' && file.progress && (
                        <div className="w-20">
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                              style={{ width: `${file.progress}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // 미리보기 로직
                        }}
                        className="p-1 hover:bg-gray-100 rounded"
                      >
                        <Eye className="h-4 w-4 text-gray-400" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // 다운로드 로직
                        }}
                        className="p-1 hover:bg-gray-100 rounded"
                      >
                        <Download className="h-4 w-4 text-gray-400" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDelete(file.id);
                        }}
                        className="p-1 hover:bg-gray-100 rounded"
                      >
                        <Trash2 className="h-4 w-4 text-gray-400" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 선택된 파일 정보 */}
      {selectedFiles.length > 0 && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">
              {selectedFiles.length}개 파일 선택됨
            </span>
            <div className="flex items-center space-x-2">
              <button className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                <Download className="h-4 w-4 mr-1" />
                다운로드
              </button>
              <button className="inline-flex items-center px-3 py-1.5 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50">
                <Trash2 className="h-4 w-4 mr-1" />
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileManager;
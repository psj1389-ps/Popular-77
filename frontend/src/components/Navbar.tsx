import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Menu, X, Search, Settings, User, LogOut, LogIn, BarChart3, History, FileText } from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';

const Navbar = () => {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const { user, signOut, loading } = useAuthContext();

  const handleSignOut = async () => {
    await signOut();
    setIsUserMenuOpen(false);
  };

  return (
    <nav className="bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* 로고 */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-12 h-12 rounded-full overflow-hidden">
              <img 
                src="https://trae-api-sg.mchost.guru/api/ide/v1/text_to_image?prompt=circular%20purple%20logo%20with%20white%20text%20%2277%20TOOLS%22%20modern%20design%20clean%20typography&image_size=square" 
                alt="77 TOOLS Logo" 
                className="w-full h-full object-cover"
              />
            </div>
            <span className="text-xl font-bold text-gray-900">
              77+ Popular Tools
            </span>
          </Link>

          {/* 네비게이션 메뉴 */}
          <div className="hidden md:flex items-center space-x-6">
            {user && (
              <>
                <Link
                  to="/dashboard"
                  className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors duration-200"
                >
                  <BarChart3 className="w-4 h-4" />
                  <span>대시보드</span>
                </Link>
                <Link
                  to="/history"
                  className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors duration-200"
                >
                  <History className="w-4 h-4" />
                  <span>기록</span>
                </Link>
                <Link
                  to="/settings"
                  className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors duration-200"
                >
                  <Settings className="w-4 h-4" />
                  <span>설정</span>
                </Link>
              </>
            )}
          </div>

          {/* 검색창 */}
          <div className="flex-1 flex justify-center px-2 lg:ml-6 lg:justify-end">
            <div className="max-w-md w-full lg:max-w-xs">
              <label htmlFor="search" className="sr-only">Search</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" aria-hidden="true" />
                </div>
                <input
                  id="search"
                  name="search"
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Search"
                  type="search"
                />
              </div>
            </div>
          </div>

          {/* 사용자 메뉴 */}
          <div className="ml-4 flex items-center space-x-4">
            {loading ? (
              <div className="w-8 h-8 rounded-full bg-gray-200 animate-pulse"></div>
            ) : user ? (
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center space-x-2 p-2 rounded-full hover:bg-gray-100 transition-colors duration-200"
                >
                  {user.user_metadata?.avatar_url ? (
                    <img
                      src={user.user_metadata.avatar_url}
                      alt="프로필"
                      className="w-8 h-8 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <span className="hidden sm:block text-sm font-medium text-gray-700">
                    {user.user_metadata?.name || user.user_metadata?.full_name || '사용자'}
                  </span>
                </button>

                {/* 드롭다운 메뉴 */}
                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-200">
                    <Link
                      to="/profile"
                      onClick={() => setIsUserMenuOpen(false)}
                      className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <User className="w-4 h-4 mr-2" />
                      내 프로필
                    </Link>
                    
                    {/* 모바일에서만 보이는 메뉴들 */}
                    <div className="md:hidden border-t border-gray-100 mt-1 pt-1">
                      <Link
                        to="/dashboard"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <BarChart3 className="w-4 h-4 mr-2" />
                        대시보드
                      </Link>
                      <Link
                        to="/history"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <History className="w-4 h-4 mr-2" />
                        기록
                      </Link>
                      <Link
                        to="/settings"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <Settings className="w-4 h-4 mr-2" />
                        설정
                      </Link>
                    </div>
                    
                    <div className="border-t border-gray-100 mt-1 pt-1">
                      <button
                        onClick={handleSignOut}
                        className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <LogOut className="w-4 h-4 mr-2" />
                        로그아웃
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <Link
                to="/login"
                className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors duration-200"
              >
                <LogIn className="w-4 h-4" />
                <span>로그인</span>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* 모바일에서 사용자 메뉴가 열렸을 때 배경 클릭으로 닫기 */}
      {isUserMenuOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsUserMenuOpen(false)}
        />
      )}
    </nav>
  );
};

export default Navbar;
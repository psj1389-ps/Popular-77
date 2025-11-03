const StatCard = ({ title, value, subtitle, icon, color = 'blue' }) => {
  const getColorClasses = (color) => {
    const colorMap = {
      blue: {
        bg: 'bg-blue-50',
        border: 'border-blue-200',
        text: 'text-black',
        icon: 'text-blue-600',
        accent: 'bg-blue-500'
      },
      green: {
        bg: 'bg-green-50',
        border: 'border-green-200',
        text: 'text-black',
        icon: 'text-green-600',
        accent: 'bg-green-500'
      },
      purple: {
        bg: 'bg-purple-50',
        border: 'border-purple-200',
        text: 'text-black',
        icon: 'text-purple-600',
        accent: 'bg-purple-500'
      },
      orange: {
        bg: 'bg-orange-50',
        border: 'border-orange-200',
        text: 'text-black',
        icon: 'text-orange-600',
        accent: 'bg-orange-500'
      },
      red: {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-black',
        icon: 'text-red-600',
        accent: 'bg-red-500'
      },
      indigo: {
        bg: 'bg-indigo-50',
        border: 'border-indigo-200',
        text: 'text-black',
        icon: 'text-indigo-600',
        accent: 'bg-indigo-500'
      },
      cyan: {
        bg: 'bg-cyan-50',
        border: 'border-cyan-200',
        text: 'text-black',
        icon: 'text-cyan-600',
        accent: 'bg-cyan-500'
      },
      pink: {
        bg: 'bg-pink-50',
        border: 'border-pink-200',
        text: 'text-black',
        icon: 'text-pink-600',
        accent: 'bg-pink-500'
      }
    };
    return colorMap[color] || colorMap.blue;
  };

  const colors = getColorClasses(color);

  return (
    <div className="relative p-4 lg:p-5 xl:p-6 rounded-lg bg-white shadow-lg shadow-black/30 hover:shadow-xl transition-all duration-300 overflow-hidden">
      {/* 장식적 요소 */}
      <div className={`absolute top-0 left-0 w-1 h-full ${colors.accent}`}></div>
      
      <div className="text-center">
        <div className="flex items-center justify-center space-x-1 mb-2">
          {icon && (
            <div className={`text-lg lg:text-xl ${colors.icon}`}>
              {icon}
            </div>
          )}
          <p className="text-xs lg:text-sm font-semibold text-black uppercase tracking-wide">{title}</p>
        </div>
        <p className="text-xl lg:text-2xl xl:text-3xl font-bold mb-1 leading-none text-black">{value.toLocaleString()}</p>
        {subtitle && (
          <p className="text-xs lg:text-sm text-black font-medium">{subtitle}</p>
        )}
      </div>
    </div>
  );
};

export default StatCard;
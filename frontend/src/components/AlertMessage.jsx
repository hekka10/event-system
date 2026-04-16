import { AlertCircle, CheckCircle2, Info, TriangleAlert } from 'lucide-react';

const VARIANT_CONFIG = {
  success: {
    className: 'border-emerald-100 bg-emerald-50 text-emerald-700',
    icon: CheckCircle2,
  },
  error: {
    className: 'border-red-100 bg-red-50 text-red-600',
    icon: AlertCircle,
  },
  warning: {
    className: 'border-amber-100 bg-amber-50 text-amber-700',
    icon: TriangleAlert,
  },
  info: {
    className: 'border-indigo-100 bg-indigo-50 text-indigo-700',
    icon: Info,
  },
};

const SIZE_CLASS_NAMES = {
  default: 'rounded-2xl p-4 text-sm',
  compact: 'rounded-xl p-3 text-sm',
};

const joinClassNames = (...classNames) => classNames.filter(Boolean).join(' ');

function AlertMessage({
  variant = 'info',
  size = 'default',
  title,
  children,
  actions,
  centered = false,
  showIcon = false,
  icon: iconOverride,
  className = '',
}) {
  const config = VARIANT_CONFIG[variant] || VARIANT_CONFIG.info;
  const Icon = iconOverride || config.icon;

  return (
    <div
      className={joinClassNames(
        'border',
        SIZE_CLASS_NAMES[size] || SIZE_CLASS_NAMES.default,
        config.className,
        className
      )}
    >
      <div
        className={joinClassNames(
          'flex gap-3',
          centered ? 'items-center justify-center text-center' : 'items-start'
        )}
      >
        {showIcon && <Icon className="mt-0.5 h-4 w-4 flex-shrink-0" />}
        <div className="min-w-0">
          {title && <p className="font-semibold">{title}</p>}
          {children && (
            <div className={joinClassNames(title && 'mt-1')}>
              {children}
            </div>
          )}
        </div>
      </div>

      {actions && (
        <div className={joinClassNames('mt-3', centered && 'flex justify-center')}>
          {actions}
        </div>
      )}
    </div>
  );
}

export default AlertMessage;

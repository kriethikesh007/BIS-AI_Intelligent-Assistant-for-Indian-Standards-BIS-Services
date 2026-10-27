import React from 'react';
import { cn } from '../../utils/cn';

/* ─── Button ─── */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, disabled, icon, children, ...props }, ref) => {
    const base = 'inline-flex items-center justify-center font-medium transition-all duration-150 rounded-lg focus-visible:outline-none select-none disabled:opacity-45 disabled:cursor-not-allowed active:scale-[0.99] cursor-pointer';

    const variants: Record<string, string> = {
      primary: 'text-white shadow-xs hover:opacity-95',
      secondary: 'border shadow-xs hover:opacity-90',
      ghost: 'hover:opacity-80',
      outline: 'border shadow-xs hover:opacity-90',
      danger: 'text-white shadow-xs hover:opacity-95',
    };

    const sizes: Record<string, string> = {
      xs: 'h-7 px-2.5 text-xs gap-1',
      sm: 'h-8 px-3 text-xs gap-1.5',
      md: 'h-9 px-3.5 text-xs font-medium gap-2',
      lg: 'h-10 px-4 text-sm font-medium gap-2',
    };

    const colorStyles: Record<string, React.CSSProperties> = {
      primary: {
        backgroundColor: 'var(--color-brand)',
        color: '#ffffff',
      },
      secondary: {
        backgroundColor: 'var(--color-bg-secondary)',
        borderColor: 'var(--color-border-default)',
        color: 'var(--color-text-primary)',
      },
      ghost: {
        backgroundColor: 'transparent',
        color: 'var(--color-text-secondary)',
      },
      outline: {
        backgroundColor: 'transparent',
        borderColor: 'var(--color-border-default)',
        color: 'var(--color-text-primary)',
      },
      danger: {
        backgroundColor: 'var(--color-error)',
        color: '#ffffff',
      },
    };

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        style={colorStyles[variant]}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
            <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor" className="opacity-75" />
          </svg>
        ) : icon ? (
          <span className="shrink-0 flex items-center">{icon}</span>
        ) : null}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

/* ─── Input ─── */
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  rightElement?: React.ReactNode;
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, icon, rightElement, error, ...props }, ref) => {
    return (
      <div className="relative w-full">
        {icon && (
          <span
            className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none flex items-center text-text-tertiary"
          >
            {icon}
          </span>
        )}
        <input
          ref={ref}
          className={cn(
            'w-full h-9 px-3 text-xs sm:text-sm rounded-lg border outline-none transition-all duration-150',
            'placeholder:text-text-tertiary',
            'focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20',
            icon && 'pl-9',
            rightElement && 'pr-10',
            className
          )}
          style={{
            backgroundColor: 'var(--color-bg-primary)',
            borderColor: error ? 'var(--color-error)' : 'var(--color-border-default)',
            color: 'var(--color-text-primary)',
          }}
          {...props}
        />
        {rightElement && (
          <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center">
            {rightElement}
          </div>
        )}
        {error && (
          <p className="mt-1 text-[11px]" style={{ color: 'var(--color-error)' }}>{error}</p>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

/* ─── Textarea ─── */
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <div className="w-full">
        <textarea
          ref={ref}
          className={cn(
            'w-full px-3 py-2 text-xs sm:text-sm rounded-lg border outline-none transition-all duration-150 resize-none',
            'placeholder:text-text-tertiary',
            'focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20',
            className
          )}
          style={{
            backgroundColor: 'var(--color-bg-primary)',
            borderColor: error ? 'var(--color-error)' : 'var(--color-border-default)',
            color: 'var(--color-text-primary)',
          }}
          {...props}
        />
        {error && (
          <p className="mt-1 text-[11px]" style={{ color: 'var(--color-error)' }}>{error}</p>
        )}
      </div>
    );
  }
);
Textarea.displayName = 'Textarea';

/* ─── Badge ─── */
export interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'brand';
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
}

export function Badge({ variant = 'default', children, className, dot }: BadgeProps) {
  const styles: Record<string, { bg: string; color: string; border: string }> = {
    default: {
      bg: 'var(--color-bg-tertiary)',
      color: 'var(--color-text-secondary)',
      border: 'var(--color-border-default)',
    },
    success: {
      bg: 'var(--color-success-bg)',
      color: 'var(--color-success)',
      border: 'rgba(22, 163, 74, 0.25)',
    },
    warning: {
      bg: 'var(--color-warning-bg)',
      color: 'var(--color-warning)',
      border: 'rgba(245, 158, 11, 0.25)',
    },
    error: {
      bg: 'var(--color-error-bg)',
      color: 'var(--color-error)',
      border: 'rgba(239, 68, 68, 0.25)',
    },
    info: {
      bg: 'var(--color-info-bg)',
      color: 'var(--color-info)',
      border: 'rgba(37, 99, 235, 0.25)',
    },
    brand: {
      bg: 'var(--color-brand-subtle)',
      color: 'var(--color-text-brand)',
      border: 'rgba(37, 99, 235, 0.25)',
    },
  };

  const st = styles[variant] || styles.default;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-medium rounded-md border tracking-tight select-none',
        className
      )}
      style={{
        backgroundColor: st.bg,
        color: st.color,
        borderColor: st.border,
      }}
    >
      {dot && (
        <span
          className="w-1.5 h-1.5 rounded-full shrink-0"
          style={{ backgroundColor: st.color }}
        />
      )}
      {children}
    </span>
  );
}

/* ─── Card ─── */
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  padding?: 'none' | 'xs' | 'sm' | 'md' | 'lg';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, hover, padding = 'md', children, ...props }, ref) => {
    const paddings = {
      none: '',
      xs: 'p-2.5',
      sm: 'p-3.5',
      md: 'p-4 sm:p-5',
      lg: 'p-6 sm:p-7',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl border transition-all duration-150',
          paddings[padding],
          hover && 'cursor-pointer hover:border-border-strong hover:shadow-xs',
          className
        )}
        style={{
          backgroundColor: 'var(--color-bg-elevated)',
          borderColor: 'var(--color-border-default)',
          boxShadow: 'var(--shadow-xs)',
        }}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = 'Card';

/* ─── Skeleton ─── */
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-pulse rounded-md', className)}
      style={{ backgroundColor: 'var(--color-bg-tertiary)' }}
      {...props}
    />
  );
}

/* ─── EmptyState ─── */
export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      {icon && (
        <div
          className="mb-3.5 p-2.5 rounded-xl border flex items-center justify-center"
          style={{
            backgroundColor: 'var(--color-bg-secondary)',
            borderColor: 'var(--color-border-default)',
            color: 'var(--color-text-secondary)',
          }}
        >
          {icon}
        </div>
      )}
      <h3 className="text-sm font-semibold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
        {title}
      </h3>
      {description && (
        <p className="text-xs max-w-sm mt-1 mb-4 leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
          {description}
        </p>
      )}
      {action}
    </div>
  );
}

/* ─── ErrorState ─── */
export interface ErrorStateProps {
  title?: string;
  message: string;
  retry?: () => void;
}

export function ErrorState({ title = 'Action could not be completed', message, retry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div
        className="mb-3.5 p-2.5 rounded-xl border flex items-center justify-center"
        style={{
          backgroundColor: 'var(--color-error-bg)',
          borderColor: 'rgba(239, 68, 68, 0.25)',
          color: 'var(--color-error)',
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>{title}</h3>
      <p className="text-xs max-w-sm mt-1 mb-3.5 leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>{message}</p>
      {retry && (
        <Button variant="secondary" size="xs" onClick={retry}>
          Retry Request
        </Button>
      )}
    </div>
  );
}

/* ─── LoadingSpinner ─── */
export function LoadingSpinner({ size = 18, className }: { size?: number; className?: string }) {
  return (
    <svg
      className={cn('animate-spin', className)}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={{ color: 'var(--color-brand)' }}
    >
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2.5" className="opacity-20" />
      <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor" />
    </svg>
  );
}

/* ─── PageLoader ─── */
export function PageLoader() {
  return (
    <div className="flex items-center justify-center h-48 w-full">
      <LoadingSpinner size={24} />
    </div>
  );
}

/* ─── Dialog / Modal ─── */
export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export function Dialog({ open, onClose, title, description, children, footer }: DialogProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 flex items-center justify-center p-4" style={{ zIndex: 'var(--z-modal)' as unknown as number }}>
      <div className="fixed inset-0 bg-black/45 backdrop-blur-xs transition-opacity" onClick={onClose} />
      <div
        className="relative w-full max-w-md rounded-xl border p-5 shadow-xl animate-in fade-in-0 zoom-in-95 duration-150"
        style={{
          backgroundColor: 'var(--color-bg-elevated)',
          borderColor: 'var(--color-border-default)',
        }}
      >
        {title && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              {title}
            </h3>
            {description && (
              <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary)' }}>
                {description}
              </p>
            )}
          </div>
        )}
        <div className="text-xs sm:text-sm">{children}</div>
        {footer && <div className="mt-4 pt-3 border-t flex justify-end gap-2" style={{ borderColor: 'var(--color-border-subtle)' }}>{footer}</div>}
      </div>
    </div>
  );
}

/**
 * Reusable Button component with Satisfactory-inspired industrial styling
 */
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost'
  size?: 'default' | 'sm' | 'lg'
}

export function Button({
  className,
  variant = 'default',
  size = 'default',
  children,
  ...props
}: ButtonProps) {
  const variants = {
    default: 'bg-satisfactory-orange text-primary-foreground hover:bg-satisfactory-yellow border-2 border-satisfactory-orange hover:border-satisfactory-yellow font-bold uppercase tracking-wide glow-orange transition-all',
    destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90 border-2 border-destructive font-bold uppercase tracking-wide',
    outline: 'border-2 border-satisfactory-panel-border bg-satisfactory-panel hover:bg-muted hover:border-satisfactory-cyan hover:text-satisfactory-cyan font-bold uppercase tracking-wide transition-all',
    secondary: 'bg-satisfactory-cyan text-secondary-foreground hover:bg-satisfactory-cyan/80 border-2 border-satisfactory-cyan glow-cyan font-bold uppercase tracking-wide transition-all',
    ghost: 'hover:bg-muted hover:text-satisfactory-orange uppercase tracking-wide transition-all',
  }

  const sizes = {
    default: 'h-10 px-4 py-2',
    sm: 'h-9 px-3 text-xs',
    lg: 'h-11 px-8 text-base',
  }

  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-satisfactory-orange focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-40 disabled:grayscale relative overflow-hidden',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}


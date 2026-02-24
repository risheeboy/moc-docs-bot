import React from 'react';
import '../styles/StatsCard.css';

interface StatsCardProps {
  title: string;
  value: number | string;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon,
  color = 'primary',
}) => {
  const isPositive = change && change >= 0;

  return (
    <div className={`stats-card stats-card-${color}`}>
      {icon && <div className="stats-icon">{icon}</div>}
      <div className="stats-content">
        <h4 className="stats-title">{title}</h4>
        <div className="stats-value">{value}</div>
        {change !== undefined && (
          <div className={`stats-change ${isPositive ? 'positive' : 'negative'}`}>
            <span className="change-arrow">{isPositive ? '↑' : '↓'}</span>
            <span className="change-value">{Math.abs(change)}%</span>
            {changeLabel && <span className="change-label">{changeLabel}</span>}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatsCard;

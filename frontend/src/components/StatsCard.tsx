import React from 'react';

export interface StatsCardProps {
  title: string;
  value: string | number;
  subtext: string;
  icon: React.ReactNode;
  iconBgClass?: string;
  tag?: string;
  actionButton?: React.ReactNode;
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  subtext,
  icon,
  iconBgClass = 'icon-blue',
  tag,
  actionButton,
}) => {
  return (
    <div className="card stats-card">
      <div className="card-header">
        <div className="card-title">
          <div className={`card-icon ${iconBgClass}`}>{icon}</div>
          <span>{title}</span>
        </div>
        {actionButton && <div className="card-action">{actionButton}</div>}
      </div>
      <div className="card-value">{value}</div>
      <div className="card-subtext">{subtext}</div>
      {tag && <div className="tag-placeholder">{tag}</div>}
    </div>
  );
};

export default StatsCard;

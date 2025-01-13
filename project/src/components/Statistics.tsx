import React from 'react';
import { BarChart3, PieChart, TrendingUp } from 'lucide-react';
import { Email } from '../types';

interface StatisticsProps {
  emails: Email[];
}

const Statistics: React.FC<StatisticsProps> = ({ emails }) => {
  const totalEmails = emails.length;
  const spamCount = emails.filter(e => e.is_spam).length;
  const adsCount = emails.filter(e => e.is_ads).length;
  
  const categoryCount = emails.reduce((acc, email) => {
    acc[email.category] = (acc[email.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const priorityCount = emails.reduce((acc, email) => {
    acc[email.priority] = (acc[email.priority] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {/* Email Categories */}
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <PieChart className="h-6 w-6 text-gray-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Categories
                </dt>
                <dd className="flex items-baseline">
                  <div className="flex flex-wrap gap-2 mt-2">
                    {Object.entries(categoryCount).map(([category, count]) => (
                      <span
                        key={category}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {category}: {count}
                      </span>
                    ))}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Priority Distribution */}
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUp className="h-6 w-6 text-gray-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Priority Distribution
                </dt>
                <dd className="flex items-baseline">
                  <div className="flex flex-wrap gap-2 mt-2">
                    {Object.entries(priorityCount).map(([priority, count]) => (
                      <span
                        key={priority}
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          priority === 'High' 
                            ? 'bg-red-100 text-red-800'
                            : priority === 'Medium'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {priority}: {count}
                      </span>
                    ))}
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>

      {/* Spam & Ads */}
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BarChart3 className="h-6 w-6 text-gray-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Spam & Ads
                </dt>
                <dd className="flex items-baseline">
                  <div className="flex flex-wrap gap-2 mt-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      Spam: {spamCount}
                    </span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      Ads: {adsCount}
                    </span>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Clean: {totalEmails - spamCount - adsCount}
                    </span>
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Statistics;
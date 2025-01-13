import React from 'react';
import { Mail, AlertTriangle, Tag } from 'lucide-react';
import { Email } from '../types';

interface EmailListProps {
  emails: Email[];
  loading: boolean;
}

const EmailList: React.FC<EmailListProps> = ({ emails, loading }) => {
  if (loading) {
    return (
      <div className="p-4">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (emails.length === 0) {
    return (
      <div className="p-8 text-center">
        <Mail className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No emails</h3>
        <p className="mt-1 text-sm text-gray-500">No emails found in this category.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden">
      <ul className="divide-y divide-gray-200">
        {emails.map((email) => (
          <li key={email.id} className="p-4 hover:bg-gray-50">
            <div className="flex items-start space-x-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {email.from_addr}
                  </p>
                  <div className="flex items-center space-x-1">
                    {email.is_spam && (
                      <AlertTriangle className="w-4 h-4 text-red-500" />
                    )}
                    {email.is_ads && (
                      <Tag className="w-4 h-4 text-yellow-500" />
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-900 font-medium mt-1">
                  {email.subject}
                </p>
                <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                  {email.summary}
                </p>
                <div className="mt-2 flex items-center space-x-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    email.priority === 'High' 
                      ? 'bg-red-100 text-red-800'
                      : email.priority === 'Medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {email.priority}
                  </span>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {email.category}
                  </span>
                </div>
              </div>
              <div className="flex-shrink-0 text-sm text-gray-500">
                {new Date(email.date_str).toLocaleDateString()}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default EmailList;
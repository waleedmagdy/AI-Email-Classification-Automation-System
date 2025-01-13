import React, { useState } from 'react';
import { MessageSquare, Send, X } from 'lucide-react';
import { Email } from '../types';

interface RecommendedRepliesProps {
  emails: Email[];
}

const RecommendedReplies: React.FC<RecommendedRepliesProps> = ({ emails }) => {
  const [sending, setSending] = useState<Record<number, boolean>>({});

  const handleSendReply = async (emailId: number) => {
    setSending(prev => ({ ...prev, [emailId]: true }));
    try {
      // In a real app, this would call your Python backend
      await fetch(`http://localhost:8000/api/emails/${emailId}/send-reply`, {
        method: 'POST',
      });
      // Remove from list on success
      setSending(prev => {
        const newState = { ...prev };
        delete newState[emailId];
        return newState;
      });
    } catch (error) {
      console.error('Error sending reply:', error);
      setSending(prev => ({ ...prev, [emailId]: false }));
    }
  };

  if (emails.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center">
          <MessageSquare className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No pending replies</h3>
          <p className="mt-1 text-sm text-gray-500">
            All recommended replies have been sent.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Recommended Replies</h2>
      </div>
      <ul className="divide-y divide-gray-200">
        {emails.map((email) => (
          <li key={email.id} className="p-4">
            <div className="space-y-2">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    To: {email.from_addr}
                  </p>
                  <p className="text-sm text-gray-500">
                    Re: {email.subject}
                  </p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleSendReply(email.id)}
                    disabled={sending[email.id]}
                    className={`inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-full 
                      ${sending[email.id]
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                      }`}
                  >
                    {sending[email.id] ? (
                      <span className="flex items-center">
                        Sending...
                      </span>
                    ) : (
                      <span className="flex items-center">
                        <Send className="w-4 h-4 mr-1" />
                        Send
                      </span>
                    )}
                  </button>
                  <button className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-full text-gray-700 bg-gray-100 hover:bg-gray-200">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <p className="text-sm text-gray-600 bg-gray-50 rounded p-3">
                {email.recommended_reply}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default RecommendedReplies;
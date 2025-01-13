import React, { useState, useEffect } from 'react';
import { Mail, Trash2, AlertTriangle, Tag, MessageSquare } from 'lucide-react';
import EmailList from './components/EmailList';
import Statistics from './components/Statistics';
import RecommendedReplies from './components/RecommendedReplies';
import { Email } from './types';

function App() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'all' | 'spam' | 'ads'>('all');

  useEffect(() => {
    // In a real app, this would fetch from your Python backend
    const fetchEmails = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/emails');
        const data = await response.json();
        setEmails(data);
      } catch (error) {
        console.error('Error fetching emails:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEmails();
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchEmails, 10000);
    return () => clearInterval(interval);
  }, []);

  const filteredEmails = emails.filter(email => {
    if (activeTab === 'spam') return email.is_spam;
    if (activeTab === 'ads') return email.is_ads;
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Mail className="w-8 h-8" />
            Email Management System
          </h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Statistics Panel */}
          <div className="lg:col-span-3">
            <Statistics emails={emails} />
          </div>

          {/* Email List Panel */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="border-b border-gray-200">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab('all')}
                    className={`${
                      activeTab === 'all'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } flex-1 py-4 px-1 text-center border-b-2 font-medium`}
                  >
                    <Mail className="w-5 h-5 mx-auto mb-1" />
                    All Emails
                  </button>
                  <button
                    onClick={() => setActiveTab('spam')}
                    className={`${
                      activeTab === 'spam'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } flex-1 py-4 px-1 text-center border-b-2 font-medium`}
                  >
                    <AlertTriangle className="w-5 h-5 mx-auto mb-1" />
                    Spam
                  </button>
                  <button
                    onClick={() => setActiveTab('ads')}
                    className={`${
                      activeTab === 'ads'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } flex-1 py-4 px-1 text-center border-b-2 font-medium`}
                  >
                    <Tag className="w-5 h-5 mx-auto mb-1" />
                    Ads
                  </button>
                </nav>
              </div>
              <EmailList emails={filteredEmails} loading={loading} />
            </div>
          </div>

          {/* Recommended Replies Panel */}
          <div className="lg:col-span-1">
            <RecommendedReplies emails={emails.filter(email => email.recommended_reply && !email.reply_sent)} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
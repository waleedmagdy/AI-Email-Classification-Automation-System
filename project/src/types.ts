export interface Email {
  id: number;
  from_addr: string;
  subject: string;
  date_str: string;
  body: string;
  category: string;
  priority: 'High' | 'Medium' | 'Low';
  is_spam: boolean;
  is_ads: boolean;
  summary: string;
  recommended_reply: string | null;
  reply_sent: boolean;
}
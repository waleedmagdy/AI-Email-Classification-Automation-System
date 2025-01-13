import unittest
from ingestion import fetch_emails_from_imap

class TestFetchEmailsFromImap(unittest.TestCase):
    pass

def test_fetch_emails_from_imap_no_emails(self):
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_mail = mock_imap.return_value
        mock_mail.login.return_value = ('OK', [b'Login successful'])
        mock_mail.select.return_value = ('OK', [b'0'])
        mock_mail.search.return_value = ('OK', [b''])

        result = fetch_emails_from_imap(
            imap_server='test.server.com',
            imap_user='testuser',
            imap_password='testpass',
            mailbox_folder='INBOX',
            search_criteria='UNSEEN',
            mark_as_seen=False
        )

        self.assertEqual(result, [])
        mock_mail.login.assert_called_once_with('testuser', 'testpass')
        mock_mail.select.assert_called_once_with('INBOX')
        mock_mail.search.assert_called_once_with(None, 'UNSEEN')
        mock_mail.fetch.assert_not_called()
        mock_mail.logout.assert_called_once()

def test_fetch_emails_from_imap_connection_error(self):
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_imap.side_effect = imaplib.IMAP4.error('Connection failed')

        result = fetch_emails_from_imap(
            imap_server='test.server.com',
            imap_user='testuser',
            imap_password='testpass',
            mailbox_folder='INBOX',
            search_criteria='UNSEEN',
            mark_as_seen=False
        )

        self.assertEqual(result, [])
        mock_imap.assert_called_once_with('test.server.com')

def test_fetch_emails_from_imap_with_attachments(self):
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_mail = mock_imap.return_value
        mock_mail.login.return_value = ('OK', [b'Login successful'])
        mock_mail.select.return_value = ('OK', [b'1'])
        mock_mail.search.return_value = ('OK', [b'1'])
        mock_mail.fetch.return_value = ('OK', [(b'1 (RFC822 {1000}', b'Raw email data'), b')'])

        with patch('ingestion.process_email') as mock_process_email:
            mock_process_email.return_value = {
                'subject': 'Test Subject',
                'from': 'sender@example.com',
                'attachments': [{'filename': 'test.txt', 'data_b64': 'SGVsbG8gV29ybGQ='}]
            }

            result = fetch_emails_from_imap(
                imap_server='test.server.com',
                imap_user='testuser',
                imap_password='testpass',
                mailbox_folder='INBOX',
                search_criteria='UNSEEN',
                mark_as_seen=False
            )

        self.assertEqual(len(result), 1)
        self.assertIn('attachments', result[0])
        self.assertEqual(len(result[0]['attachments']), 1)
        self.assertEqual(result[0]['attachments'][0]['filename'], 'test.txt')
        self.assertEqual(result[0]['attachments'][0]['data_b64'], 'SGVsbG8gV29ybGQ=')

        mock_mail.login.assert_called_once_with('testuser', 'testpass')
        mock_mail.select.assert_called_once_with('INBOX')
        mock_mail.search.assert_called_once_with(None, 'UNSEEN')
        mock_mail.fetch.assert_called_once()
        mock_mail.logout.assert_called_once()

def test_fetch_emails_from_imap_invalid_mailbox(self):
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_mail = mock_imap.return_value
        mock_mail.login.return_value = ('OK', [b'Login successful'])
        mock_mail.select.side_effect = imaplib.IMAP4.error('Invalid mailbox')

        result = fetch_emails_from_imap(
            imap_server='test.server.com',
            imap_user='testuser',
            imap_password='testpass',
            mailbox_folder='INVALID_FOLDER',
            search_criteria='UNSEEN',
            mark_as_seen=False
        )

        self.assertEqual(result, [])
        mock_mail.login.assert_called_once_with('testuser', 'testpass')
        mock_mail.select.assert_called_once_with('INVALID_FOLDER')
        mock_mail.search.assert_not_called()
        mock_mail.fetch.assert_not_called()
        mock_mail.logout.assert_called_once()

def test_fetch_emails_from_imap_non_ascii_content(self):
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_mail = mock_imap.return_value
        mock_mail.login.return_value = ('OK', [b'Login successful'])
        mock_mail.select.return_value = ('OK', [b'1'])
        mock_mail.search.return_value = ('OK', [b'1'])
        
        # Create a mock email with non-ASCII content
        non_ascii_subject = "Súbjèct with àccents"
        non_ascii_body = "Cöntent with ñön-ASCII chàráctèrs"
        mock_email = MagicMock()
        mock_email.get.side_effect = lambda x: non_ascii_subject if x == "Subject" else "sender@example.com"
        
        with patch('email.message_from_bytes', return_value=mock_email):
            with patch('ingestion.process_email') as mock_process_email:
                mock_process_email.return_value = {
                    'subject': non_ascii_subject,
                    'from': 'sender@example.com',
                    'body': non_ascii_body
                }
                
                mock_mail.fetch.return_value = ('OK', [(b'1 (RFC822 {1000}', b'Raw email data'), b')'])
                
                result = fetch_emails_from_imap(
                    imap_server='test.server.com',
                    imap_user='testuser',
                    imap_password='testpass',
                    mailbox_folder='INBOX',
                    search_criteria='UNSEEN',
                    mark_as_seen=False
                )
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['subject'], non_ascii_subject)
        self.assertEqual(result[0]['body'], non_ascii_body)
        self.assertIsInstance(result[0]['subject'], str)
        self.assertIsInstance(result[0]['body'], str)

def test_fetch_emails_from_imap_custom_search_criteria(self):
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_mail = mock_imap.return_value
        mock_mail.login.return_value = ('OK', [b'Login successful'])
        mock_mail.select.return_value = ('OK', [b'1'])
        mock_mail.search.return_value = ('OK', [b'1 2'])
        mock_mail.fetch.side_effect = [
            ('OK', [(b'1 (RFC822 {1000}', b'Raw email data 1'), b')']),
            ('OK', [(b'2 (RFC822 {1000}', b'Raw email data 2'), b')'])
        ]

        with patch('ingestion.process_email') as mock_process_email:
            mock_process_email.side_effect = [
                {'subject': 'Test Subject 1', 'from': 'sender1@example.com'},
                {'subject': 'Test Subject 2', 'from': 'sender2@example.com'}
            ]

            result = fetch_emails_from_imap(
                imap_server='test.server.com',
                imap_user='testuser',
                imap_password='testpass',
                mailbox_folder='INBOX',
                search_criteria='SUBJECT "Important"',
                mark_as_seen=True
            )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['subject'], 'Test Subject 1')
        self.assertEqual(result[1]['subject'], 'Test Subject 2')
        self.assertEqual(result[0]['imap_msg_id'], '1')
        self.assertEqual(result[1]['imap_msg_id'], '2')

        mock_mail.login.assert_called_once_with('testuser', 'testpass')
        mock_mail.select.assert_called_once_with('INBOX')
        mock_mail.search.assert_called_once_with(None, 'SUBJECT "Important"')
        self.assertEqual(mock_mail.fetch.call_count, 2)
        mock_mail.store.assert_has_calls([
            call(b'1', '+FLAGS', '\\Seen'),
            call(b'2', '+FLAGS', '\\Seen')
        ])
        mock_mail.logout.assert_called_once()

def test_fetch_emails_from_imap_mark_as_seen(self):
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_mail = mock_imap.return_value
        mock_mail.login.return_value = ('OK', [b'Login successful'])
        mock_mail.select.return_value = ('OK', [b'1'])
        mock_mail.search.return_value = ('OK', [b'1 2'])
        mock_mail.fetch.return_value = ('OK', [(b'1 (RFC822 {1000}', b'Raw email data'), b')'])

        with patch('ingestion.process_email') as mock_process_email:
            mock_process_email.return_value = {'subject': 'Test Subject', 'from': 'sender@example.com'}

            result = fetch_emails_from_imap(
                imap_server='test.server.com',
                imap_user='testuser',
                imap_password='testpass',
                mailbox_folder='INBOX',
                search_criteria='UNSEEN',
                mark_as_seen=True
            )

        self.assertTrue(len(result) > 0)
        mock_mail.store.assert_called_with(b'1', "+FLAGS", "\\Seen")
        mock_mail.store.assert_called_with(b'2', "+FLAGS", "\\Seen")
        self.assertEqual(mock_mail.store.call_count, 2)

if __name__ == '__main__':
    unittest.main()

def test_fetch_emails_from_imap_leave_unseen(self):
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_mail = mock_imap.return_value
        mock_mail.login.return_value = ('OK', [b'Login successful'])
        mock_mail.select.return_value = ('OK', [b'1'])
        mock_mail.search.return_value = ('OK', [b'1 2 3'])
        mock_mail.fetch.return_value = ('OK', [(b'1 (RFC822 {1000}', b'Raw email data'), b')'])

        with patch('ingestion.process_email') as mock_process_email:
            mock_process_email.return_value = {'subject': 'Test Subject', 'from': 'sender@example.com'}

            fetch_emails_from_imap(
                imap_server='test.server.com',
                imap_user='testuser',
                imap_password='testpass',
                mailbox_folder='INBOX',
                search_criteria='UNSEEN',
                mark_as_seen=False
            )

        mock_mail.store.assert_not_called()

def test_fetch_emails_from_imap_different_folder(self):
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        mock_mail = mock_imap.return_value
        mock_mail.login.return_value = ('OK', [b'Login successful'])
        mock_mail.select.return_value = ('OK', [b'1'])
        mock_mail.search.return_value = ('OK', [b'1'])
        mock_mail.fetch.return_value = ('OK', [(b'1 (RFC822 {1000}', b'Raw email data'), b')'])

        with patch('ingestion.process_email') as mock_process_email:
            mock_process_email.return_value = {'subject': 'Test Subject', 'from': 'sender@example.com'}

            result = fetch_emails_from_imap(
                imap_server='test.server.com',
                imap_user='testuser',
                imap_password='testpass',
                mailbox_folder='SENT',
                search_criteria='ALL',
                mark_as_seen=True
            )

        self.assertTrue(len(result) > 0)
        mock_mail.login.assert_called_once_with('testuser', 'testpass')
        mock_mail.select.assert_called_once_with('SENT')
        mock_mail.search.assert_called_once_with(None, 'ALL')
        mock_mail.fetch.assert_called()
        mock_mail.store.assert_called_once_with(b'1', '+FLAGS', '\\Seen')
        mock_process_email.assert_called()
        self.assertIn('imap_msg_id', result[0])
        self.assertEqual(result[0]['subject'], 'Test Subject')
        self.assertEqual(result[0]['from'], 'sender@example.com')
        mock_mail.logout.assert_called_once()

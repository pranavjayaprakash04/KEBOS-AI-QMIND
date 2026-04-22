import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import toast from 'react-hot-toast';

interface Message {
  message_id: string;
  sender_id: string;
  receiver_id: string;
  message_type: string;
  status: string;
  timestamp: string;
  text?: string;
  filename?: string;
  file_size?: number;
}

interface User {
  id: string;
  username: string;
  email: string;
}

interface Channel {
  channel_id: string;
  created_at: string;
}


export function SecureMessagingPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [messageText, setMessageText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [activeChannel, setActiveChannel] = useState<string | null>(null);

  // Fetch users
  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      try {
        // In a real implementation, this would fetch from the backend
        // const response = await apiClient.get('/api/users');
        // return response.data;
        
        // Mock data for demonstration
        return [
          { id: '1', username: 'alice', email: 'alice@example.com' },
          { id: '2', username: 'bob', email: 'bob@example.com' },
          { id: '3', username: 'charlie', email: 'charlie@example.com' },
        ];
      } catch (error) {
        console.error('Failed to fetch users:', error);
        throw error;
      }
    },
  });

  // Generate keypair mutation

  // Create secure channel mutation

  // Send text message mutation

  // Send file message mutation

  // Fetch messages for selected user
  const { data: messages, isLoading: messagesLoading } = useQuery<Message[]>({
    queryKey: ['messages', selectedUser?.id],
    queryFn: async () => {
      if (!selectedUser) return [];
      
      try {
        // In a real implementation, this would fetch from the backend
        // const response = await apiClient.get(`/messaging/messages/${selectedUser.id}`);
        // return response.data;
        
        // Mock data for demonstration
        return [
          {
            message_id: '1',
            sender_id: user?.id || '0',
            receiver_id: selectedUser.id,
            message_type: 'text',
            status: 'delivered',
            timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
            text: 'Hello, this is a secure message using post-quantum encryption!',
          },
          {
            message_id: '2',
            sender_id: selectedUser.id,
            receiver_id: user?.id || '0',
            message_type: 'text',
            status: 'read',
            timestamp: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
            text: 'Thanks for the secure message. This is really cool!',
          },
          {
            message_id: '3',
            sender_id: user?.id || '0',
            receiver_id: selectedUser.id,
            message_type: 'file',
            status: 'delivered',
            timestamp: new Date(Date.now() - 1 * 60 * 1000).toISOString(),
            filename: 'secure_document.pdf',
            file_size: 1024 * 1024,
          },
        ];
      } catch (error) {
        console.error('Failed to fetch messages:', error);
        throw error;
      }
    },
    enabled: !!selectedUser,
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  // Fetch channels
  const { data: channels } = useQuery<Channel[]>({
    queryKey: ['channels'],
    queryFn: async () => {
      try {
        // In a real implementation, this would fetch from the backend
        // const response = await apiClient.get('/messaging/channels');
        // return response.data;
        
        // Mock data for demonstration
        return [
          { channel_id: 'channel1', created_at: new Date().toISOString() },
          { channel_id: 'channel2', created_at: new Date().toISOString() },
        ];
      } catch (error) {
        console.error('Failed to fetch channels:', error);
        throw error;
      }
    },
  });

  // Generate keypair mutation
  const generateKeypairMutation = useMutation({
    mutationFn: async () => {
      try {
        const response = await apiClient.post('/messaging/keypair');
        return response.data;
      } catch (error) {
        console.error('Failed to generate keypair:', error);
        throw error;
      }
    },
    onSuccess: () => {
      toast.success('Keypair generated successfully');
    },
    onError: (error) => {
      toast.error(`Failed to generate keypair: ${error.message}`);
    },
  });

  // Create secure channel mutation
  const createChannelMutation = useMutation({
    mutationFn: async (receiverId: string) => {
      try {
        const response = await apiClient.post('/messaging/channel', { receiver_id: receiverId });
        return response.data;
      } catch (error) {
        console.error('Failed to create secure channel:', error);
        throw error;
      }
    },
    onSuccess: (data) => {
      setActiveChannel(data.channel_id);
      toast.success('Secure channel established');
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
    onError: (error) => {
      toast.error(`Failed to create secure channel: ${error.message}`);
    },
  });

  // Send text message mutation
  const sendTextMessageMutation = useMutation({
    mutationFn: async ({ receiverId, text, channelId }: { receiverId: string; text: string; channelId?: string }) => {
      try {
        const response = await apiClient.post('/messaging/send/text', {
          receiver_id: receiverId,
          text,
          channel_id: channelId,
        });
        return response.data;
      } catch (error) {
        console.error('Failed to send message:', error);
        throw error;
      }
    },
    onSuccess: () => {
      setMessageText('');
      toast.success('Message sent');
      queryClient.invalidateQueries({ queryKey: ['messages', selectedUser?.id] });
    },
    onError: (error) => {
      toast.error(`Failed to send message: ${error.message}`);
    },
  });

  // Send file message mutation
  const sendFileMutation = useMutation({
    mutationFn: async ({ receiverId, file, channelId }: { receiverId: string; file: File; channelId?: string }) => {
      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('receiver_id', receiverId);
        if (channelId) {
          formData.append('channel_id', channelId);
        }

        const response = await apiClient.post('/messaging/send/file', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        return response.data;
      } catch (error) {
        console.error('Failed to send file:', error);
        throw error;
      }
    },
    onSuccess: () => {
      setFile(null);
      toast.success('File sent');
      queryClient.invalidateQueries({ queryKey: ['messages', selectedUser?.id] });
    },
    onError: (error) => {
      toast.error(`Failed to send file: ${error.message}`);
    },
  });

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Handle user selection
  const handleUserSelect = (user: User) => {
    setSelectedUser(user);
    // Find existing channel with this user
    const existingChannel = channels?.find(channel => channel.channel_id.includes(user.id));
    if (existingChannel) {
      setActiveChannel(existingChannel.channel_id);
    } else {
      setActiveChannel(null);
    }
  };

  // Handle send message
  const handleSendMessage = () => {
    if (!selectedUser || !messageText.trim()) return;

    sendTextMessageMutation.mutate({
      receiverId: selectedUser.id,
      text: messageText,
      channelId: activeChannel || undefined,
    });
  };

  // Handle send file
  const handleSendFile = () => {
    if (!selectedUser || !file) return;

    sendFileMutation.mutate({
      receiverId: selectedUser.id,
      file,
      channelId: activeChannel || undefined,
    });
  };

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  // Create secure channel
  const handleCreateChannel = () => {
    if (!selectedUser) return;
    createChannelMutation.mutate(selectedUser.id);
  };

  // Generate keypair
  const handleGenerateKeypair = () => {
    generateKeypairMutation.mutate();
  };

  return (
    <div className="min-h-screen">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-black mb-2">Secure Messaging</h1>
        <p className="text-gray-600">End-to-end encrypted messaging with post-quantum cryptography</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* User list */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className="card-hover p-4 lg:col-span-1 shadow-md hover:shadow-lg transition-shadow duration-300"
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-black">Contacts</h3>
            <button 
              onClick={handleGenerateKeypair}
              className="btn-secondary text-sm py-1 px-2 hover:shadow-md transition-shadow duration-200"
            >
              Generate Keypair
            </button>
          </div>
          
          {usersLoading ? (
            <div className="flex justify-center py-8">
              <p className="text-black">Loading users...</p>
            </div>
          ) : users && users.length > 0 ? (
            <ul className="space-y-2">
              {users.map((user) => (
                <li key={user.id}>
                  <button
                    onClick={() => handleUserSelect(user)}
                    className={`w-full text-left p-3 rounded-lg transition-all duration-200 hover:shadow-md ${selectedUser?.id === user.id ? 'bg-primary-dark text-white shadow-lg' : 'hover:bg-background-light'}`}
                  >
                    <div className="flex items-center">
                      <div className="w-8 h-8 rounded-full bg-quaternary text-white flex items-center justify-center mr-3">
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className={`font-medium ${selectedUser?.id === user.id ? 'text-white' : 'text-black'}`}>{user.username}</p>
                        <p className={`text-xs ${selectedUser?.id === user.id ? 'text-gray-200' : 'text-black opacity-70'}`}>{user.email}</p>
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex justify-center py-8">
              <p className="text-black">No users available</p>
            </div>
          )}
        </motion.div>

        {/* Message area */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="card-hover p-4 lg:col-span-3 shadow-md hover:shadow-lg transition-shadow duration-300"
        >
          {selectedUser ? (
            <>
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center">
                  <div className="w-10 h-10 rounded-full bg-quaternary text-white flex items-center justify-center mr-3">
                    {selectedUser.username.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-black">{selectedUser.username}</h3>
                    <p className="text-xs text-black opacity-70">{selectedUser.email}</p>
                  </div>
                </div>
                <div>
                  {activeChannel ? (
                    <div className="flex items-center text-success text-sm">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      <span>Secure Channel Active</span>
                    </div>
                  ) : (
                    <button 
                      onClick={handleCreateChannel}
                      className="btn-primary text-sm hover:shadow-md transition-shadow duration-200"
                      disabled={createChannelMutation.isPending}
                    >
                      {createChannelMutation.isPending ? 'Creating...' : 'Create Secure Channel'}
                    </button>
                  )}
                </div>
              </div>

              {/* Messages */}
              <div className="bg-background-light rounded-lg p-4 h-96 overflow-y-auto mb-4">
                {messagesLoading ? (
                  <div className="flex justify-center py-8">
                    <p className="text-black">Loading messages...</p>
                  </div>
                ) : messages && messages.length > 0 ? (
                  <div className="space-y-4">
                    {messages.map((message) => {
                      const isOutgoing = message.sender_id === user?.id;
                      return (
                        <motion.div 
                          key={message.message_id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.2 }}
                          className={`flex ${isOutgoing ? 'justify-end' : 'justify-start'}`}
                        >
                          <div 
                            className={`max-w-xs lg:max-w-md rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow duration-200 ${isOutgoing ? 'bg-primary-dark text-white' : 'bg-background-secondary text-black'}`}
                          >
                            {message.message_type === 'text' && message.text && (
                              <p>{message.text}</p>
                            )}
                            {message.message_type === 'file' && message.filename && (
                              <div className="flex items-center space-x-2">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                <div>
                                  <p className="text-sm font-medium">{message.filename}</p>
                                  <p className="text-xs">{(message.file_size! / 1024).toFixed(1)} KB</p>
                                </div>
                              </div>
                            )}
                            <p className={`text-xs mt-1 ${isOutgoing ? 'text-gray-300' : 'text-gray-500'}`}>
                              {formatTimestamp(message.timestamp)}
                              {message.status === 'delivered' && (
                                <span className="ml-2">✓</span>
                              )}
                              {message.status === 'read' && (
                                <span className="ml-2">✓✓</span>
                              )}
                            </p>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full">
                    <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    <p className="text-gray-500">No messages yet</p>
                    <p className="text-black text-sm mt-1">Send a message to start the conversation</p>
                  </div>
                )}
              </div>

              {/* Message input */}
              <div className="flex space-x-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    placeholder="Type a secure message..."
                    className="w-full p-3 rounded-lg border border-light-accent focus:ring-2 focus:ring-primary-dark focus:border-transparent"
                    onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                  />
                  <label htmlFor="file-upload" className="absolute right-3 top-3 cursor-pointer text-gray-500 hover:text-primary-dark">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                    </svg>
                    <input
                      id="file-upload"
                      type="file"
                      className="hidden"
                      onChange={handleFileChange}
                    />
                  </label>
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={!messageText.trim() || sendTextMessageMutation.isPending}
                  className="btn-primary px-4 hover:shadow-md transition-shadow duration-200"
                >
                  {sendTextMessageMutation.isPending ? (
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  )}
                </button>
              </div>

              {/* File preview */}
              {file && (
                <div className="mt-2 p-2 bg-background-light rounded-lg flex items-center justify-between">
                  <div className="flex items-center">
                    <svg className="w-5 h-5 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div>
                      <p className="text-sm font-medium text-black">{file.name}</p>
                      <p className="text-xs text-black opacity-70">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleSendFile}
                      disabled={sendFileMutation.isPending}
                      className="btn-primary text-xs py-1 px-2 hover:shadow-md transition-shadow duration-200"
                    >
                      {sendFileMutation.isPending ? 'Sending...' : 'Send'}
                    </button>
                    <button
                      onClick={() => setFile(null)}
                      className="text-gray-500 hover:text-error"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-96">
              <svg className="w-24 h-24 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <h3 className="text-xl font-semibold text-black mb-2">Select a contact</h3>
              <p className="text-black text-center max-w-md">
                Choose a contact from the list to start a secure, end-to-end encrypted conversation using post-quantum cryptography.
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}
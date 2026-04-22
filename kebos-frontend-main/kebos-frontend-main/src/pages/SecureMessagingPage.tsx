import { useState, useRef } from 'react';
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
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [messageText, setMessageText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [activeChannel, setActiveChannel] = useState<string | null>(null);

  // Fetch users
  const { data: users, isLoading: usersLoading } = useQuery<User[]>({
    queryKey: ['users'],
    queryFn: async (): Promise<User[]> => {
      try {
        // Fetch real users from backend API
        const response = await apiClient.get('/api/auth/users');
        return response.data;
      } catch (error) {
        console.error('Failed to fetch users:', error);
        // Return empty array instead of mock data
        return [];
      }
    },
  });

  // Fetch messages for selected user
  const { data: messages, isLoading: messagesLoading } = useQuery<Message[]>({
    queryKey: ['messages', selectedUser?.id],
    queryFn: async (): Promise<Message[]> => {
      try {
        // Fetch real messages from backend API
        if (!selectedUser) return [];
        const response = await apiClient.get(`/api/messaging/messages?user=${selectedUser.id}`);
        return response.data;
      } catch (error) {
        console.error('Failed to fetch messages:', error);
        return [];
      }
    },
    enabled: !!selectedUser,
    refetchInterval: 10000,
  });

  // Fetch channels
  const { data: channels } = useQuery<Channel[]>({
    queryKey: ['channels'],
    queryFn: async (): Promise<Channel[]> => {
      try {
        // Fetch real channels from backend API
        const response = await apiClient.get('/api/messaging/channels');
        return response.data;
      } catch (error) {
        console.error('Failed to fetch channels:', error);
        return [];
      }
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

  // Create channel mutation
  const createChannelMutation = useMutation({
    mutationFn: async (receiverId: string) => {
      try {
        const response = await apiClient.post('/messaging/channels', {
          receiver_id: receiverId,
        });
        return response.data;
      } catch (error) {
        console.error('Failed to create channel:', error);
        throw error;
      }
    },
    onSuccess: (data) => {
      setActiveChannel(data.channel_id);
      toast.success('Secure channel created');
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
    onError: (error) => {
      toast.error(`Failed to create channel: ${error.message}`);
    },
  });

  // Generate keypair mutation
  const generateKeypairMutation = useMutation({
    mutationFn: async () => {
      try {
        const response = await apiClient.post('/messaging/keypair/generate');
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
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-black mb-2">Secure Messaging</h1>
        <p className="text-gray-600">End-to-end encrypted messaging with post-quantum cryptography</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-200px)]">
        {/* Contacts sidebar */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className="bg-white rounded-lg border border-gray-200 p-6 lg:col-span-1 shadow-sm hover:shadow-md transition-shadow duration-300"
        >
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-semibold text-black">Contacts</h3>
            <button 
              onClick={handleGenerateKeypair}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm font-medium"
            >
              Generate Keypair
            </button>
          </div>
          
          {usersLoading ? (
            <div className="flex justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                <p className="text-gray-600">Loading contacts...</p>
              </div>
            </div>
          ) : users && users.length > 0 ? (
            <ul className="space-y-3">
              {users.map((user) => (
                <li key={user.id}>
                  <button
                    onClick={() => handleUserSelect(user)}
                    className={`w-full text-left p-4 rounded-lg transition-all duration-200 hover:shadow-sm ${
                      selectedUser?.id === user.id 
                        ? 'bg-blue-50 border-2 border-blue-200 shadow-sm' 
                        : 'hover:bg-gray-50 border-2 border-transparent'
                    }`}
                  >
                    <div className="flex items-center">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-4 text-white font-semibold ${
                        selectedUser?.id === user.id ? 'bg-blue-600' : 'bg-gray-500'
                      }`}>
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className={`font-medium ${selectedUser?.id === user.id ? 'text-blue-900' : 'text-black'}`}>
                          {user.username}
                        </p>
                        <p className={`text-sm ${selectedUser?.id === user.id ? 'text-blue-700' : 'text-gray-600'}`}>
                          {user.email}
                        </p>
                      </div>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex justify-center py-12">
              <div className="text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <p className="text-gray-600">No contacts available</p>
              </div>
            </div>
          )}
        </motion.div>

        {/* Message area */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="bg-white rounded-lg border border-gray-200 p-6 lg:col-span-3 shadow-sm hover:shadow-md transition-shadow duration-300"
        >
          {selectedUser ? (
            <div className="flex flex-col h-full">
              {/* Chat header */}
              <div className="flex justify-between items-center pb-4 border-b border-gray-200 mb-4">
                <div className="flex items-center">
                  <div className="w-12 h-12 rounded-full bg-blue-600 text-white flex items-center justify-center mr-4 font-semibold">
                    {selectedUser.username.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-black">{selectedUser.username}</h3>
                    <p className="text-sm text-gray-600">{selectedUser.email}</p>
                  </div>
                </div>
                <div>
                  {activeChannel ? (
                    <div className="flex items-center text-green-600 text-sm bg-green-50 px-3 py-2 rounded-lg">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                      </svg>
                      <span className="font-medium">Secure Channel Active</span>
                    </div>
                  ) : (
                    <button 
                      onClick={handleCreateChannel}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200 text-sm font-medium"
                      disabled={createChannelMutation.isPending}
                    >
                      {createChannelMutation.isPending ? 'Creating...' : 'Create Secure Channel'}
                    </button>
                  )}
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 bg-gray-50 rounded-lg p-4 overflow-y-auto mb-4">
                {messagesLoading ? (
                  <div className="flex justify-center py-12">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                      <p className="text-gray-600">Loading messages...</p>
                    </div>
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
                            className={`max-w-xs lg:max-w-md rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow duration-200 ${
                              isOutgoing 
                                ? 'bg-blue-600 text-white' 
                                : 'bg-white text-black border border-gray-200'
                            }`}
                          >
                            {message.message_type === 'text' && message.text && (
                              <p className="text-base">{message.text}</p>
                            )}
                            {message.message_type === 'file' && message.filename && (
                              <div className="flex items-center space-x-3">
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                <div>
                                  <p className="text-sm font-medium">{message.filename}</p>
                                  <p className="text-xs opacity-70">{(message.file_size! / 1024).toFixed(1)} KB</p>
                                </div>
                              </div>
                            )}
                            <p className={`text-xs mt-2 ${isOutgoing ? 'text-blue-100' : 'text-gray-500'}`}>
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
                    <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center mb-4">
                      <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                    </div>
                    <p className="text-gray-500 text-lg font-medium">No messages yet</p>
                    <p className="text-gray-400 text-sm mt-1">Send a message to start the conversation</p>
                  </div>
                )}
              </div>

              {/* Message input */}
              <div className="flex space-x-3">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={messageText}
                    onChange={(e) => setMessageText(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                    placeholder="Type your message..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black bg-white resize-none"
                    disabled={!activeChannel}
                  />
                </div>
                
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  className="hidden"
                  disabled={!activeChannel}
                />
                
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-3 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={!activeChannel}
                  title="Attach file"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                  </svg>
                </button>
                
                <button
                  onClick={handleSendMessage}
                  disabled={!messageText.trim() || !activeChannel || sendTextMessageMutation.isPending}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {sendTextMessageMutation.isPending ? 'Sending...' : 'Send'}
                </button>
              </div>
              
              {file && (
                <div className="mt-3 flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div>
                      <p className="text-sm font-medium text-black">{file.name}</p>
                      <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleSendFile}
                      disabled={sendFileMutation.isPending}
                      className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50"
                    >
                      {sendFileMutation.isPending ? 'Sending...' : 'Send File'}
                    </button>
                    <button
                      onClick={() => setFile(null)}
                      className="text-gray-500 hover:text-red-600 transition-colors duration-200"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-96">
              <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center mb-6">
                <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-black mb-2">Select a contact</h3>
              <p className="text-gray-600 text-center max-w-md">
                Choose a contact from the list to start a secure, end-to-end encrypted conversation using post-quantum cryptography.
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
}

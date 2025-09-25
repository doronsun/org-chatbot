import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Loader2, Mic, Square } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  isLoading, 
  disabled = false 
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !disabled) {
      onSendMessage(message);
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky bottom-0 bg-gradient-to-t from-dark-900/95 to-transparent backdrop-blur-sm p-4"
    >
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="relative">
          <div className="glass rounded-2xl p-4 shadow-2xl">
            <div className="flex items-end gap-3">
              {/* Text Input */}
              <div className="flex-1 relative">
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="כתבו את השאלה שלכם כאן..."
                  disabled={disabled || isLoading}
                  className="w-full bg-transparent text-white placeholder-white/50 resize-none outline-none text-lg leading-relaxed min-h-[24px] max-h-32"
                  rows={1}
                />
              </div>

              {/* Send Button */}
              <motion.button
                type="submit"
                disabled={!message.trim() || isLoading || disabled}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`p-3 rounded-xl transition-all duration-200 ${
                  message.trim() && !isLoading && !disabled
                    ? 'bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white shadow-lg'
                    : 'bg-white/10 text-white/30 cursor-not-allowed'
                }`}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </motion.button>
            </div>

            {/* Helpful Tips */}
            {!message.trim() && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-3 text-sm text-white/60 text-center"
              >
                💡 נסו לשאול על נושאים עסקיים, טכנולוגיה, או כל דבר שמעניין אתכם
              </motion.div>
            )}
          </div>
        </div>
      </form>
    </motion.div>
  );
};

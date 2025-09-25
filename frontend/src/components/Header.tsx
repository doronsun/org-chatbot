import React from 'react';
import { motion } from 'framer-motion';
import { Bot, Sparkles, Settings, Trash2 } from 'lucide-react';

interface HeaderProps {
  onClearChat: () => void;
  messageCount: number;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onClearChat, messageCount, isLoading }) => {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky top-0 z-10 bg-gradient-to-r from-dark-900/95 to-dark-800/95 backdrop-blur-md border-b border-white/10"
    >
      <div className="max-w-6xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-4">
            <motion.div
              animate={{ rotate: isLoading ? 360 : 0 }}
              transition={{ duration: 2, repeat: isLoading ? Infinity : 0, ease: "linear" }}
              className="relative"
            >
              <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <Bot className="w-6 h-6 text-white" />
              </div>
              {isLoading && (
                <div className="absolute inset-0 rounded-xl border-2 border-primary-400 animate-ping" />
              )}
            </motion.div>
            
            <div>
              <h1 className="text-2xl font-bold gradient-text">
                עוזר ארגוני חכם
              </h1>
              <p className="text-white/60 text-sm">
                בינה מלאכותית מתקדמת לעסקים
              </p>
            </div>
          </div>

          {/* Stats & Actions */}
          <div className="flex items-center gap-4">
            {/* Message Counter */}
            <div className="hidden md:flex items-center gap-2 px-3 py-2 bg-white/10 rounded-lg">
              <Sparkles className="w-4 h-4 text-primary-400" />
              <span className="text-sm text-white/80">
                {messageCount} הודעות
              </span>
            </div>

            {/* Clear Chat Button */}
            <motion.button
              onClick={onClearChat}
              disabled={messageCount === 0}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`p-2 rounded-lg transition-all duration-200 ${
                messageCount > 0
                  ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400 hover:text-red-300'
                  : 'bg-white/5 text-white/30 cursor-not-allowed'
              }`}
              title="נקה את השיחה"
            >
              <Trash2 className="w-5 h-5" />
            </motion.button>

            {/* Settings Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition-all duration-200"
              title="הגדרות"
            >
              <Settings className="w-5 h-5" />
            </motion.button>
          </div>
        </div>
      </div>
    </motion.header>
  );
};

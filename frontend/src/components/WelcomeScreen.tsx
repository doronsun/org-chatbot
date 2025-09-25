import React from 'react';
import { motion } from 'framer-motion';
import { 
  MessageCircle, 
  Zap, 
  Shield, 
  Brain, 
  ArrowLeft,
  Lightbulb,
  Target,
  Users
} from 'lucide-react';

interface WelcomeScreenProps {
  onStartChat: (suggestion: string) => void;
}

const suggestions = [
  {
    icon: Lightbulb,
    title: "רעיונות עסקיים",
    description: "איך לפתח מוצר חדש?",
    prompt: "איך אני יכול לפתח מוצר חדש לעסק שלי?"
  },
  {
    icon: Target,
    title: "אסטרטגיה",
    description: "תכנון שיווק דיגיטלי",
    prompt: "אני רוצה לתכנן קמפיין שיווק דיגיטלי, איך מתחילים?"
  },
  {
    icon: Users,
    title: "ניהול צוות",
    description: "איך לנהל צוות יעיל?",
    prompt: "איך אני יכול לשפר את הניהול של הצוות שלי?"
  },
  {
    icon: Brain,
    title: "טכנולוגיה",
    description: "AI וחדשנות",
    prompt: "איך בינה מלאכותית יכולה לעזור לעסק שלי?"
  }
];

const features = [
  {
    icon: Zap,
    title: "מהיר ויעיל",
    description: "תשובות מהירות ומדויקות"
  },
  {
    icon: Shield,
    title: "בטוח ואמין",
    description: "המידע שלכם מוגן"
  },
  {
    icon: Brain,
    title: "חכם ומתקדם",
    description: "בינה מלאכותית מתקדמת"
  }
];

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onStartChat }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-4xl mx-auto px-4 py-8"
    >
      {/* Hero Section */}
      <div className="text-center mb-12">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="w-20 h-20 bg-gradient-to-r from-primary-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-2xl"
        >
          <MessageCircle className="w-10 h-10 text-white" />
        </motion.div>
        
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="text-4xl md:text-5xl font-bold text-white mb-4"
        >
          ברוכים הבאים לעוזר החכם
        </motion.h2>
        
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-xl text-white/70 mb-8 max-w-2xl mx-auto leading-relaxed"
        >
          העוזר הארגוני שלכם עם בינה מלאכותית מתקדמת. 
          שאלו כל שאלה וקבלו תשובות מקצועיות ומהירות.
        </motion.p>
      </div>

      {/* Features */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="grid md:grid-cols-3 gap-6 mb-12"
      >
        {features.map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 + index * 0.1 }}
            className="glass rounded-xl p-6 text-center hover:bg-white/20 transition-all duration-300"
          >
            <feature.icon className="w-8 h-8 text-primary-400 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
            <p className="text-white/70 text-sm">{feature.description}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* Suggestions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
      >
        <h3 className="text-2xl font-bold text-white mb-6 text-center">
          התחילו עם אחת מהשאלות האלה:
        </h3>
        
        <div className="grid md:grid-cols-2 gap-4">
          {suggestions.map((suggestion, index) => (
            <motion.button
              key={suggestion.title}
              onClick={() => onStartChat(suggestion.prompt)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.8 + index * 0.1 }}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              className="glass rounded-xl p-6 text-right hover:bg-white/20 transition-all duration-300 group"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-primary-600 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                  <suggestion.icon className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h4 className="text-lg font-semibold text-white mb-1 group-hover:text-primary-300 transition-colors">
                    {suggestion.title}
                  </h4>
                  <p className="text-white/60 text-sm mb-2">{suggestion.description}</p>
                  <div className="flex items-center gap-2 text-primary-400 text-sm">
                    <ArrowLeft className="w-4 h-4" />
                    <span>לחץ לשאלה</span>
                  </div>
                </div>
              </div>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
};

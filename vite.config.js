import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        roiPredictor: resolve(__dirname, 'roi-predictor.html'),
        leadAuditor: resolve(__dirname, 'lead-auditor.html'),
        securityQuiz: resolve(__dirname, 'security-quiz.html'),
        blogVoiceAi: resolve(__dirname, 'blog-voice-ai.html'),
        blogRealEstateAi: resolve(__dirname, 'blog-real-estate-ai.html'),
        blogRoiSme: resolve(__dirname, 'blog-roi-sme.html'),
        blogPost: resolve(__dirname, 'blog-post.html'),
        aloriaGroup: resolve(__dirname, 'aloria-group.html'),
        admin: resolve(__dirname, 'admin.html'),
      },
    },
  },
});

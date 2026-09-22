// 目录: ./frontend/tailwind.config.js | 模块: 样式配置 | 职责: 配置 Tailwind CSS 扫描路径
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
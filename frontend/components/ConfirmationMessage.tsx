import React from 'react';
// 修正：從共享的 types.ts 檔案導入 ConfirmationMessageProps 型別
import { ConfirmationMessageProps } from '../types';

/**
 * 顯示表單已建立的確認訊息，並提供連結。
 * @param formUrl - 要顯示的 Google 表單連結。
 */
const ConfirmationMessage: React.FC<ConfirmationMessageProps> = ({ formUrl }) => {

  const handleCopyLink = () => {
    // 使用 navigator.clipboard API 來複製連結
    navigator.clipboard.writeText(formUrl).then(() => {
      alert('連結已複製！'); // 這裡可以使用更美觀的提示框
    }, (err) => {
      console.error('無法複製連結: ', err);
      // 向後兼容的複製方法
      try {
        const textArea = document.createElement('textarea');
        textArea.value = formUrl;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        alert('連結已複製！');
      } catch (e) {
         console.error('備用複製方法失敗', e);
      }
    });
  };

  return (
    <div className="bg-green-100 border-l-4 border-green-500 text-green-700 p-4 rounded-lg my-4 shadow-md">
      <p className="font-bold">表單已成功建立！</p>
      <p className="mt-2">您可以分享以下連結給您的朋友：</p>
      <div className="mt-3 flex items-center space-x-2">
        <input
          type="text"
          readOnly
          value={formUrl}
          className="flex-grow bg-white border border-gray-300 rounded-md px-3 py-2 text-sm text-gray-800"
        />
        <button
          onClick={handleCopyLink}
          className="bg-green-500 text-white rounded-md px-4 py-2 text-sm font-semibold hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
        >
          複製連結
        </button>
      </div>
       <a
        href={formUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-green-600 hover:text-green-800 mt-2 inline-block"
       >
         或點此直接前往表單 &rarr;
       </a>
    </div>
  );
};

export default ConfirmationMessage;

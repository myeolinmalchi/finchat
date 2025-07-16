// TODO: 삭제
// export const chatMock = {
//   title: '디폴트는 내용 요약되어 들어감',
//   question: '대출 상품 추천해줘.',
//   answer: [
//     {
//       paragraph:
//         '주거안정 월세 대출은 무주택 국민의 월세를 지원하는 대출입니다. 대출 신청자는 민법상 성년인 세대원 중 1인 이상이어야 하며, 전세자금 대출이나 주택담보대출을 받은 경우에는 대출 신청이 불가합니다. 대출금은 최대 960만원까지 지원되며, 대출 기간은 2년입니다.',
//       urls: [
//         'https://obank.kbstar.com/quics?page=C103998&cc=b104363:b104516&i=isNew=N&prcode=LN200000076&QSL=F',
//       ],
//     },
//     {
//       paragraph:
//         "안녕. '청년 전용 버팀목 전월세 대출'은 무주택 청년가구의 전월세 지원을 위한 상품입니다. 대출 한도는 최대 1,200만원이며, 대출금리는 연 1.0%에서 1.5%로 설정됩니다. 대출 신청자는 성년인 세대원 중 1인 이상이 무주택이어야 합니다. 자세한 내용은 [여기](https://obank.kbstar.com/quics?page=C103998&cc=b104363:b104516&i=isNew=N&prcode=LN400001003&QSL=F)에서 확인할 수 있습니다.",
//       urls: [
//         'https://obank.kbstar.com/quics?page=C103998&cc=b104363:b104516&i=isNew=N&prcode=LN20000300&QSL=F',
//       ],
//     },
//     {
//       paragraph: '**굵은 글자테스트**',
//       urls: [
//         'https://obank.kbstar.com/quics?page=C103998&cc=b104363:b104516&i=isNew=N&prcode=LN20000313&QSL=F',
//       ],
//     },
//     {
//       paragraph:
//         '청년전용 버팀목 전월세 대출은 무주택 청년가구의 전월세 지원을 위한 대출입니다. 대출금은 최대 1,200만원까지 가능하며, 대출 기간은 2년이고, 금리는 연 1.0%로 적용됩니다.',
//       urls: [
//         'https://obank.kbstar.com/quics?page=C103998&cc=b104363:b104516&i=isNew=N&prcode=LN400001003&QSL=F',
//       ],
//     },
//     {
//       paragraph:
//         'KB 나라사랑 대출은 국가보훈부와 협약에 따라 국가를 위해 헌신한 국가유공자 등을 위한 대출입니다. 대출금액은 최대 1억 5천만원까지 가능하며, 대출 기간은 20년이고, 금리는 연 1.0%로 적용됩니다.',
//       urls: [
//         'https://obank.kbstar.com/quics?page=C103429&cc=b104363:b104516&i=isNew=N&prcode=LN20000114&QSL=F',
//       ],
//     },
//   ],
//   messages: [
//     {
//       role: 'user',
//       content: '대출 상품 추천해줘.',
//     },
//     {
//       role: 'assistant',
//       content: [
//         {
//           paragraph:
//             '주거안정 월세 대출은 무주택 국민의 월세를 지원하는 대출입니다. 대출 신청자는 민법상 성년인 세대원 중 1인 이상이어야 하며, 전세자금 대출이나 주택담보대출을 받은 경우에는 대출 신청이 불가합니다. 대출금은 최대 960만원까지 지원되며, 대출 기간은 2년입니다.',
//           urls: [
//             'https://obank.kbstar.com/quics?page=C103998&cc=b104363:b104516&i=isNew=N&prcode=LN200000076&QSL=F',
//           ],
//         },
//         {
//           paragraph:
//             '내 집 마련 디딤돌 대출은 무주택 국민의 내 집 마련을 지원하는 대출로, 대출 신청자는 민법상 성년인 세대주여야 합니다. 대출금은 최대 1억 5천만원까지 가능하며, 대출 기간은 20년이고, 금리는 연 1.0%로 적용됩니다.',
//           urls: [
//             'https://obank.kbstar.com/quics?page=C103998&cc=b104363:b104516&i=isNew=N&prcode=LN20000300&QSL=F',
//           ],
//         },
//         {
//           paragraph:
//             '버팀목 전세자금 대출은 무주택 국민의 주거안정을 지원하는 대출입니다. 대출 신청자는 민법상 성년인 세대원 중 1인 이상이어야 하며, 대출금은 최대 1억 5천만원까지 가능하고, 대출 기간은 2년이며, 금리는 연 1.0%로 적용됩니다.',
//           urls: [
//             'https://obank.kbstar.com/quics?page=C103998&cc=b104363:b104516&i=isNew=N&prcode=LN20000313&QSL=F',
//           ],
//         },
//         {
//           paragraph:
//             '청년전용 버팀목 전월세 대출은 무주택 청년가구의 전월세 지원을 위한 대출입니다. 대출금은 최대 1,200만원까지 가능하며, 대출 기간은 2년이고, 금리는 연 1.0%로 적용됩니다.',
//           urls: [
//             'https://obank.kbstar.com/quics?page=C103998&cc=b104363:b104516&i=isNew=N&prcode=LN400001003&QSL=F',
//           ],
//         },
//         {
//           paragraph:
//             'KB 나라사랑 대출은 국가보훈부와 협약에 따라 국가를 위해 헌신한 국가유공자 등을 위한 대출입니다. 대출금액은 최대 1억 5천만원까지 가능하며, 대출 기간은 20년이고, 금리는 연 1.0%로 적용됩니다.',
//           urls: [
//             'https://obank.kbstar.com/quics?page=C103429&cc=b104363:b104516&i=isNew=N&prcode=LN20000114&QSL=F',
//           ],
//         },
//       ],
//     },
//   ],
// };

// TODO: new

export const responseMock = {
  chat_id: '6df7bd7d-5042-4523-8eaf-8822aa42fe0d',
  status: 'response',
  content: {
    products: [
      {
        product_type: 'deposit',
        description: '상품 특징 또는 간략한 설명1',
        institution: '회사/은행 이름1',
        options: [
          {
            category: '최고',
            value: '연 8.0%',
          },
          {
            category: '기본',
            value: '연 3.5%',
          },
        ],
        details:
          '병사봉급 한도 내에서 복무기간 동안 목돈마련을 원하는 병역 의무복무자 ...',
        tags: ['목돈 마련', '군적금'],
      },
      {
        product_type: 'deposit',
        description: '상품 특징 또는 간략한 설명2',
        institution: '은행이름2',
        options: [
          {
            category: '최고',
            value: '연 8.0%',
          },
          {
            category: '기본',
            value: '연 3.5%',
          },
        ],
        details:
          '병사봉급 한도 내에서 복무기간 동안 목돈마련을 원하는 병역 의무복무자 맞춤형 상품',
        tags: ['목돈 마련', '군적금'],
      },
      {
        product_type: 'deposit',
        description: '상품 특징 또는 간략한 설명3',
        institution: '회사/은행 이름3',
        options: [
          {
            category: '최고',
            value: '연 8.0%',
          },
          {
            category: '기본',
            value: '연 3.5%',
          },
        ],
        details:
          '병사봉급 한도 내에서 복무기간 동안 목돈마련을 원하는 병역 의무복무자 ...',
        tags: ['목돈 마련', '군적금'],
      },
    ],
  },
};

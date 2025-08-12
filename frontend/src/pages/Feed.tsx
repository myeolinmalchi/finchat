import linkArrow from '@/assets/feed/link-arrow.svg';

type Policy = {
  title: string;
  thumbnail: string;
  description: string;
  feed_id: string;
  type: string;
  external_url: string;
};

const mock: Policy[] = Array.from({ length: 6 }).map((_, i) => ({
  title: '서울특별시 송파구 청년정책 아카데미로 19~39세 청년 40명 모집',
  thumbnail:
    'https://t1.kakaocdn.net/thumb/C630x354.fwebp.q100/?fname=https%3A%2F%2Ft1.kakaocdn.net%2Fkakaocorp%2Fkakaocorp%2Fadmin%2Fnews%2F97b9a620019800001.jpg',
  description:
    '청년들이 지역사회의 문제를 직접 발굴하고 분석해 해결책을 제시하는 실전형 정책 참여 프로그램이다. 교육은 청년정책의 이해, 청년 주거 특강, 정책 기획 워크숍, 정책 제안서 작성 실습 등으로 구성되어 있다.',
  feed_id: String(i + 1),
  type: 'policy',
  external_url: 'https://www.google.com',
}));

export const FeedPage = () => {
  return (
    <div className="py-[120px]">
      <div className="mx-auto grid max-w-[1040px] grid-cols-1 gap-x-[28px] gap-y-[32px] sm:grid-cols-2 lg:grid-cols-3">
        {mock.map((p) => (
          <article
            key={p.feed_id}
            className="group flex h-[436px] flex-col overflow-hidden rounded-[20px] border border-gray2 bg-white shadow-[0_0_4px_0_rgba(27,27,27,0.04)]"
          >
            <div className="h-[240px]">
              <img
                src={p.thumbnail}
                alt={p.title}
                className="h-full w-full object-cover"
              />
            </div>

            <div className="flex flex-1 flex-col p-4">
              <div className="space-y-[4px]">
                <h3 className="line-clamp-3 text-[20px] font-[600] leading-[28px] text-black">
                  {p.title}
                </h3>
                <p className="text-gray7 line-clamp-4 text-[12px] font-[400] leading-[16px]">
                  {p.description}
                </p>
              </div>

              <div className="mt-auto flex justify-end pt-4">
                <a
                  href={p.external_url}
                  className="inline-flex items-center gap-[4px] rounded-[32px] bg-gray6 px-[8px] py-[4px] text-[12px] font-[500] text-gray5"
                >
                  외부링크로 바로가기
                  <img src={linkArrow} alt=">" className="h-[16px] w-[16px]" />
                </a>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
};

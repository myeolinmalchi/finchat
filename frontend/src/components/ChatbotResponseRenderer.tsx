import ReactMarkdown from 'react-markdown';

import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/pagination';
import { Navigation, Pagination } from 'swiper/modules';
import { Swiper, SwiperSlide } from 'swiper/react';

import { ChatProduct } from '@/api/chat';

import leftArrow from '@/assets/chat/left-arrow.svg';
import rightArrow from '@/assets/chat/right-arrow.svg';

interface ProductProps {
  products: ChatProduct[];
}

export const ChatbotResponseRenderer = ({ products }: ProductProps) => {
  return (
    <div className="relative mx-auto mt-6 w-[800px]">
      <button className="custom-prev left-0px absolute top-1/2 z-10 -translate-y-1/2">
        <img src={leftArrow} alt="이전" />
      </button>
      <button className="custom-next absolute right-0 top-1/2 z-10 -translate-y-1/2">
        <img src={rightArrow} alt="다음" />
      </button>

      <div className="mx-auto w-[688px]">
        <Swiper
          modules={[Navigation, Pagination]}
          slidesPerView={1}
          navigation={{
            nextEl: '.custom-next',
            prevEl: '.custom-prev',
          }}
          pagination={{
            clickable: true,
            el: '.custom-pagination',
            bulletClass: 'custom-bullet',
          }}
        >
          {products.map((product, index) => (
            <SwiperSlide key={index}>
              <div className="rounded-[12px] border border-[#EFEFEF] bg-white px-[32px] py-[36px]">
                <p className="mb-[16px] font-[600] text-gray5">
                  {product.description}
                </p>
                <div className="flex items-center gap-[4px] text-[32px] font-[600] text-[#242525]">
                  {product.product_type}
                </div>
                <p className="mb-[24px] mt-[4px] text-[16px] font-[500] text-[#515354]">
                  {product.institution}
                </p>
                <div className="mb-[12px] flex gap-[12px]">
                  {product.options?.map((opt, i) => (
                    <div key={i} className="flex items-center font-[600]">
                      <span className="mr-1 text-[12px] text-[#B2B4B7]">
                        {opt.category}
                      </span>
                      <span className="text-[24px] text-main">{opt.value}</span>
                    </div>
                  ))}
                </div>

                <div className="rounded-[8px] bg-[#F3F6F8] px-[12px] py-[20px] text-[16px] font-[400] leading-[24px] text-[#242525]">
                  <ReactMarkdown>{product.details || ''}</ReactMarkdown>

                  {/* <p className="font-[700]">저축금액</p>
                  <p>
                    월 1천원 ~ 30만원(단, 신규금액만 0원이상) <br />※ 단,
                    ‘장병내일준비적금’의 금융기관 합산 저축한도는 고객별 월
                    55만원이며,
                    <br />동 저축한도를 초과하지 않는 범위 내에서 한 은행의 월
                    저축한도는 최고 30만원까지 설정 및 입금 가능
                  </p> */}
                </div>
                <div className="mt-[24px] flex gap-[8px]">
                  {product.tags?.map((tag: string, i: number) => (
                    <span
                      key={i}
                      className="rounded-[24px] border border-main bg-[#FCFCFC] px-[12px] py-[8px] font-[600] text-[#4D4D4D]"
                    >
                      💛 {tag}
                    </span>
                  ))}
                </div>
              </div>
            </SwiperSlide>
          ))}

          <div className="custom-pagination mt-[32px] flex justify-center gap-[8px]" />
        </Swiper>
      </div>

      {/* <div className="mx-auto mt-[40px] w-[720px] text-[16px] font-[400] leading-[24px] text-[#242525]">
        여러 조건을 고려하였을 때, KB장병내일준비적금을 가장 추천드립니다.{' '}
        <br />
        이유 1. 업계 최고 수준의 우대금리 제공 <br />
        이유 2. 비대면 가입 전 과정 지원 <br />
        🎯 당신에게 특히 추천하는 이유 <br />
        빠르게 목돈을 마련하고 싶은 당신을 위해, 높은 금리의 상품을 우선적으로
        고려했습니다. <br />
        GOP 부대 특성상 외출이 제한적일 수 있으므로 비대면 가입 여부 또한
        중요하게 판단했습니다.
      </div> */}
    </div>
  );
};

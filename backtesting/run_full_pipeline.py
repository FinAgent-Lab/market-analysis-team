"""
백테스팅 데이터 수집 및 보고서 생성 파이프라인

1. 데이터 수집 (data_builder.py)
2. 주간 보고서 생성 (weekly_batch_generator.py)
"""

import os
import sys
import subprocess
from datetime import datetime

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def run_command(command: str, description: str):
    """명령어 실행 및 결과 출력"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"📋 실행 명령어: {command}")
    print(f"{'='*60}")
    
    start_time = datetime.now()
    
    try:
        subprocess.run(
            command,
            shell=True,
            cwd=os.path.dirname(__file__),
            check=True,
            capture_output=False,
            text=True
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n✅ {description} 완료!")
        print(f"⏱️  소요 시간: {duration}")
        return True
        
    except subprocess.CalledProcessError as e:
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n❌ {description} 실패!")
        print(f"⏱️  소요 시간: {duration}")
        print(f"🔍 오류 코드: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ {description} 실행 중 오류: {e}")
        return False

def main():
    """전체 파이프라인 실행"""
    print("🔬 백테스팅 데이터 수집 및 보고서 생성 파이프라인 시작")
    print(f"🕐 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    pipeline_start = datetime.now()
    success_count = 0
    total_steps = 2
    
    # Step 1: 데이터 수집
    if run_command("python data_builder.py", "백테스팅 데이터 수집"):
        success_count += 1
        print("✅ 데이터 수집이 완료되었습니다.")
    else:
        print("❌ 데이터 수집에 실패했습니다. 보고서 생성을 계속 진행합니다.")
    
    # Step 2: 주간 보고서 생성
    if run_command("python weekly_batch_generator.py", "주간 보고서 일괄 생성"):
        success_count += 1
        print("✅ 주간 보고서 생성이 완료되었습니다.")
    else:
        print("❌ 주간 보고서 생성에 실패했습니다.")
    
    # 최종 결과
    pipeline_end = datetime.now()
    total_duration = pipeline_end - pipeline_start
    
    print(f"\n{'='*80}")
    print("🎉 백테스팅 파이프라인 완료!")
    print(f"📊 성공률: {success_count}/{total_steps} ({(success_count/total_steps)*100:.1f}%)")
    print(f"⏱️  총 소요 시간: {total_duration}")
    print(f"🕐 완료 시간: {pipeline_end.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 다음 단계 안내
    print("\n📋 다음 단계:")
    print("1. 생성된 보고서 확인: python cli.py list --limit 20")
    print("2. 특정 보고서 조회: python cli.py report --ticker AAPL --date 2024-03-15")
    print("3. 데이터베이스 직접 확인 (Supabase Dashboard)")

if __name__ == "__main__":
    main()
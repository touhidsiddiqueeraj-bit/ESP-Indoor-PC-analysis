// firmware-stm32 -- STM32F103C8 (Blue Pill) measurement harness, stm32duino core
// CH341 on USART1 (PA9=TX -> CH341 RX, PA10=RX <- CH341 TX), 115200 8N1 = Serial1
// Wiring: PA8 (PWM) --jumper--> PA0 (ADC A0). If no jumper, ADC reads floating but timing still valid.
// Commands: L = latency breakdown, H = hw info, B = bench. Mirrors ESP32-S3 Table 1.
// ponytail: one env, one serial, DWT-based ns where possible

#include <Arduino.h>
#define PWM_PIN PA8
#define ADC_PIN PA0
#define ADC_FS 24.0f
#define VREF -12.0f
#define D_MIN 0.05f
#define D_MAX 0.95f
#define KP 0.05f
#define KI 100.0f
#define KD 1e-5f

// USART1 via CH341
#define CH341 Serial1

static float cpu_mhz = 72.0f;

static inline void dwt_enable(){
#if defined(DWT_BASE)
  CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
  DWT->CYCCNT = 0;
  DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
#endif
}
static inline uint32_t dwt_cc(){
#if defined(DWT_BASE)
  return DWT->CYCCNT;
#else
  return micros();
#endif
}
static inline float ns_span(uint32_t dt){
#if defined(DWT_BASE)
  return dt * 1000.0f / cpu_mhz;
#else
  return dt * 1000.0f; // us->ns
#endif
}

struct PIDF { float kp,ki,kd,ts,e1=0,e2=0,d=D_MIN; void reset(){e1=e2=0;d=D_MIN;} void step(float meas,float vref){ float e=meas-vref; float du=kp*(e-e1)+ki*ts*e+(kd/ts)*(e-2*e1+e2); e2=e1;e1=e; d=constrain(d+du,D_MIN,D_MAX); } };
static float fqabs(float x,float bits){ float q=powf(2,bits); return roundf(x/ADC_FS*q)/q*ADC_FS; }
static float fqduty(float d,float bits){ float q=powf(2,bits); return roundf(d*q)/q; }
static float read_vpin_raw(){ int raw=analogRead(ADC_PIN); return (float)raw * 3.3f / 4095.0f; }
static float vout_of(float vpin){ return -vpin * ADC_FS / 3.3f; }
static void pwm_init(){ pinMode(PWM_PIN, OUTPUT); }
static void pwm_set(float d){ int v=(int)(d*255); analogWrite(PWM_PIN, v); }

static void mode_latency(){
  const int N=3000;
  analogRead(ADC_PIN);
  uint32_t mn=0xFFFFFFFF,mx=0; uint64_t sm=0;
  for(int i=0;i<N;i++){ uint32_t a=dwt_cc(); (void)analogRead(ADC_PIN); uint32_t dt=dwt_cc()-a; if(dt<mn)mn=dt; if(dt>mx)mx=dt; sm+=dt; }
  CH341.print("CSV,L,adc_raw,"); CH341.print(ns_span(mn)); CH341.print(","); CH341.print(sm*1000.0/cpu_mhz/N); CH341.print(","); CH341.println(ns_span(mx));

  PIDF pid; pid.kp=KP; pid.ki=KI; pid.kd=KD; pid.ts=62e-6f;
  mn=0xFFFFFFFF; mx=0; sm=0;
  for(int i=0;i<N;i++){ uint32_t a=dwt_cc(); float mq=fqabs(-12.0f + (i&63)*0.01f, 8); pid.step(mq,VREF); (void)fqduty(pid.d,8); uint32_t dt=dwt_cc()-a; if(dt<mn)mn=dt; if(dt>mx)mx=dt; sm+=dt; }
  CH341.print("CSV,L,comp_f32,"); CH341.print(ns_span(mn)); CH341.print(","); CH341.print(sm*1000.0/cpu_mhz/N); CH341.print(","); CH341.println(ns_span(mx));

  mn=0xFFFFFFFF; mx=0; sm=0;
  pwm_init(); pwm_set(0.5f);
  for(int i=0;i<N;i++){ uint32_t a=dwt_cc(); pwm_set(0.25f + (i&1)*0.5f); uint32_t dt=dwt_cc()-a; if(dt<mn)mn=dt; if(dt>mx)mx=dt; sm+=dt; }
  CH341.print("CSV,L,pwm,"); CH341.print(ns_span(mn)); CH341.print(","); CH341.print(sm*1000.0/cpu_mhz/N); CH341.print(","); CH341.println(ns_span(mx));

  mn=0xFFFFFFFF; mx=0; sm=0;
  pid.reset();
  for(int i=0;i<N;i++){ uint32_t a=dwt_cc(); float meas=vout_of(read_vpin_raw()); pid.step(fqabs(meas,12),VREF); pwm_set(fqduty(pid.d,8)); uint32_t dt=dwt_cc()-a; if(dt<mn)mn=dt; if(dt>mx)mx=dt; sm+=dt; }
  CH341.print("CSV,L,step,"); CH341.print(ns_span(mn)); CH341.print(","); CH341.print(sm*1000.0/cpu_mhz/N); CH341.print(","); CH341.println(ns_span(mx));
  CH341.print("CSV,L,info,cpu_mhz,"); CH341.println(cpu_mhz);
  CH341.println("CSV,LDONE");
}
static void mode_hw(){
  CH341.println("CSV,H,note,STM32F103C8 stm32core CH341 USART1");
  CH341.print("CSV,H,cpu_mhz,"); CH341.println(cpu_mhz);
  uint32_t a=dwt_cc(); (void)analogRead(ADC_PIN); uint32_t dt=dwt_cc()-a;
  CH341.print("CSV,H,adc_one_ns,"); CH341.println(ns_span(dt));
  CH341.print("CSV,H,pwm_pin,"); CH341.println(PWM_PIN);
  CH341.print("CSV,H,adc_pin,"); CH341.println(ADC_PIN);
  CH341.println("CSV,HDONE");
}
static void mode_bench(){
  PIDF pid; pid.kp=KP; pid.ki=KI; pid.kd=KD; pid.ts=10e-6f;
  const int N=5000;
  uint32_t mn=0xFFFFFFFF,mx=0; uint64_t sm=0;
  for(int i=0;i<N;i++){ uint32_t a=dwt_cc(); float mq=fqabs(-12.0f+0.3f*sinf(i*0.01f),8); pid.step(mq,VREF); (void)fqduty(pid.d,8); uint32_t dt=dwt_cc()-a; if(dt<mn)mn=dt; if(dt>mx)mx=dt; sm+=dt; }
  CH341.print("CSV,B,bench_ns,"); CH341.print(ns_span(mn)); CH341.print(","); CH341.print(sm*1000.0/cpu_mhz/N); CH341.print(","); CH341.println(ns_span(mx));
  CH341.println("CSV,BDONE");
}

void setup(){
  dwt_enable();
#if defined(SystemCoreClock)
  cpu_mhz = SystemCoreClock / 1e6f;
#endif
  CH341.begin(115200);
  delay(800);
  CH341.println("CSV,BOOT,STM32F103C8");
  CH341.print("CSV,CPU,"); CH341.println(cpu_mhz);
  pinMode(ADC_PIN, INPUT_ANALOG);
  // stm32core 12-bit ADC
  analogReadResolution(12);
  pwm_init();
  CH341.println("CSV,READY,send L/H/B");
}
void loop(){
  if(CH341.available()){
    int c=CH341.read();
    while(CH341.available()) CH341.read();
    if(c=='L'||c=='l') mode_latency();
    else if(c=='H'||c=='h') mode_hw();
    else if(c=='B'||c=='b') mode_bench();
  }
  delay(10);
}

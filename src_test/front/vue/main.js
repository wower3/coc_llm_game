const { createApp } = Vue;

const App = {
  template: `
    <h1>COC 7th Character Generator</h1>
    <button @click="generateAttributes">随机生成属性</button>

    <h2>基础属性</h2>
    <div class="attributes-grid">
      <div v-for="(value, key) in attributes" :key="key" class="attribute-item">
        <h3>{{ key.toUpperCase() }}</h3>
        <span class="value">{{ value }}</span>
      </div>
    </div>

    <h2>衍生属性</h2>
    <div class="attributes-grid">
      <div class="derived-item">
        <h3>伤害加值 (DB)</h3>
        <span class="value">{{ damageBonus }}</span>
      </div>
      <div class="derived-item">
        <h3>体型 (Build)</h3>
        <span class="value">{{ build }}</span>
      </div>
      <div class="derived-item">
        <h3>移动 (Move)</h3>
        <span class="value">{{ move }}</span>
      </div>
      <div class="derived-item">
        <h3>幸运 (Luck)</h3>
        <span class="value">{{ luck }}</span>
      </div>
      <div class="derived-item">
        <h3>生命 (HP)</h3>
        <span class="value">{{ hp }}</span>
      </div>
      <div class="derived-item">
        <h3>理智 (SAN)</h3>
        <span class="value">{{ san }}</span>
      </div>
      <div class="derived-item">
        <h3>魔法 (MP)</h3>
        <span class="value">{{ mp }}</span>
      </div>
    </div>
  `,
  data() {
    return {
      attributes: {
        str: 0,
        con: 0,
        siz: 0,
        dex: 0,
        app: 0,
        edu: 0,
        int: 0,
        pow: 0,
      },
       luck: 0,
    };
  },
  computed: {
    hp() {
      return Math.floor((this.attributes.con + this.attributes.siz) / 10);
    },
    san() {
      return this.attributes.pow;
    },
    mp() {
      return Math.floor(this.attributes.pow / 5);
    },
    damageBonus() {
      const total = this.attributes.str + this.attributes.siz;
      if (total < 65) return "-2";
      if (total < 85) return "-1";
      if (total < 125) return "0";
      if (total < 165) return "+1d4";
      if (total < 205) return "+1d6";
      return "N/A";
    },
    build() {
      const total = this.attributes.str + this.attributes.siz;
      if (total < 65) return -2;
      if (total < 85) return -1;
      if (total < 125) return 0;
      if (total < 165) return 1;
      if (total < 205) return 2;
      return "N/A";
    },
    move() {
        if (this.attributes.dex < this.attributes.siz && this.attributes.str < this.attributes.siz) {
            return 7;
        }
        if (this.attributes.dex > this.attributes.siz && this.attributes.str > this.attributes.siz) {
            return 9;
        }
        return 8;
    }
  },
  methods: {
    rollDice(times, sides) {
      let total = 0;
      for (let i = 0; i < times; i++) {
        total += Math.floor(Math.random() * sides) + 1;
      }
      return total;
    },
    generateAttributes() {
      this.attributes.str = this.rollDice(3, 6) * 5;
      this.attributes.con = this.rollDice(3, 6) * 5;
      this.attributes.siz = (this.rollDice(2, 6) + 6) * 5;
      this.attributes.dex = this.rollDice(3, 6) * 5;
      this.attributes.app = this.rollDice(3, 6) * 5;
      this.attributes.edu = (this.rollDice(2, 6) + 6) * 5;
      this.attributes.int = (this.rollDice(2, 6) + 6) * 5;
      this.attributes.pow = this.rollDice(3, 6) * 5;
      this.luck = this.rollDice(3, 6) * 5;
    },
  },
  mounted() {
      this.generateAttributes();
  }
};

createApp(App).mount('#app');
